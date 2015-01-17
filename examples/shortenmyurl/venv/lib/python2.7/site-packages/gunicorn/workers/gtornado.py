# -*- coding: utf-8 -
#
# This file is part of gunicorn released under the MIT license.
# See the NOTICE for more information.

import os
import sys

try:
    import tornado.web
except ImportError:
    raise RuntimeError("You need tornado installed to use this worker.")
import tornado.httpserver
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.wsgi import WSGIContainer
from gunicorn.workers.base import Worker
from gunicorn import __version__ as gversion


class TornadoWorker(Worker):

    @classmethod
    def setup(cls):
        web = sys.modules.pop("tornado.web")
        old_clear = web.RequestHandler.clear

        def clear(self):
            old_clear(self)
            self._headers["Server"] += " (Gunicorn/%s)" % gversion
        web.RequestHandler.clear = clear
        sys.modules["tornado.web"] = web

    def handle_exit(self, sig, frame):
        if self.alive:
            super(TornadoWorker, self).handle_exit(sig, frame)
            self.stop()

    def handle_request(self):
        self.nr += 1
        if self.alive and self.nr >= self.max_requests:
            self.alive = False
            self.log.info("Autorestarting worker after current request.")
            self.stop()

    def watchdog(self):
        if self.alive:
            self.notify()

        if self.ppid != os.getppid():
            self.log.info("Parent changed, shutting down: %s", self)
            self.stop()

    def run(self):
        self.ioloop = IOLoop.instance()
        self.alive = True
        PeriodicCallback(self.watchdog, 1000, io_loop=self.ioloop).start()

        # Assume the app is a WSGI callable if its not an
        # instance of tornado.web.Application or is an
        # instance of tornado.wsgi.WSGIApplication
        app = self.wsgi
        if not isinstance(app, tornado.web.Application) or \
           isinstance(app, tornado.wsgi.WSGIApplication):
            app = WSGIContainer(app)

        # Monkey-patching HTTPConnection.finish to count the
        # number of requests being handled by Tornado. This
        # will help gunicorn shutdown the worker if max_requests
        # is exceeded.
        httpserver = sys.modules["tornado.httpserver"]
        if hasattr(httpserver, 'HTTPConnection'):
            old_connection_finish = httpserver.HTTPConnection.finish

            def finish(other):
                self.handle_request()
                old_connection_finish(other)
            httpserver.HTTPConnection.finish = finish
            sys.modules["tornado.httpserver"] = httpserver

            server_class = tornado.httpserver.HTTPServer
        else:

            class _HTTPServer(tornado.httpserver.HTTPServer):

                def on_close(instance, server_conn):
                    self.handle_request()
                    super(_HTTPServer, instance).on_close(server_conn)

            server_class = _HTTPServer

        if self.cfg.is_ssl:
            server = server_class(app, io_loop=self.ioloop,
                    ssl_options=self.cfg.ssl_options)
        else:
            server = server_class(app, io_loop=self.ioloop)

        self.server = server

        for s in self.sockets:
            s.setblocking(0)
            if hasattr(server, "add_socket"):  # tornado > 2.0
                server.add_socket(s)
            elif hasattr(server, "_sockets"):  # tornado 2.0
                server._sockets[s.fileno()] = s

        server.no_keep_alive = self.cfg.keepalive <= 0
        server.start(num_processes=1)

        self.ioloop.start()

    def stop(self):
        if hasattr(self, 'server'):
            try:
                self.server.stop()
            except Exception:
                pass
        PeriodicCallback(self.stop_ioloop, 1000, io_loop=self.ioloop).start()

    def stop_ioloop(self):
        if not self.ioloop._callbacks and len(self.ioloop._timeouts) <= 1:
            self.ioloop.stop()
