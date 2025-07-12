#
# This file is part of gunicorn released under the MIT license.
# See the NOTICE for more information.

import os
import sys

try:
    import tornado
except ImportError:
    raise RuntimeError("You need tornado installed to use this worker.")
import tornado.web
import tornado.httpserver
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.wsgi import WSGIContainer
from gunicorn.workers.base import Worker
from gunicorn import __version__ as gversion
from gunicorn.sock import ssl_context


# Tornado 5.0 updated its IOLoop, and the `io_loop` arguments to many
# Tornado functions have been removed in Tornado 5.0. Also, they no
# longer store PeriodCallbacks in ioloop._callbacks. Instead we store
# them on our side, and use stop() on them when stopping the worker.
# See https://www.tornadoweb.org/en/stable/releases/v5.0.0.html#backwards-compatibility-notes
# for more details.
TORNADO5 = tornado.version_info >= (5, 0, 0)


class TornadoWorker(Worker):

    @classmethod
    def setup(cls):
        web = sys.modules.pop("tornado.web")
        old_clear = web.RequestHandler.clear

        def clear(self):
            old_clear(self)
            if "Gunicorn" not in self._headers["Server"]:
                self._headers["Server"] += " (Gunicorn/%s)" % gversion
        web.RequestHandler.clear = clear
        sys.modules["tornado.web"] = web

    def handle_exit(self, sig, frame):
        if self.alive:
            super().handle_exit(sig, frame)

    def handle_request(self):
        self.nr += 1
        if self.alive and self.nr >= self.max_requests:
            self.log.info("Autorestarting worker after current request.")
            self.alive = False

    def watchdog(self):
        if self.alive:
            self.notify()

        if self.ppid != os.getppid():
            self.log.info("Parent changed, shutting down: %s", self)
            self.alive = False

    def heartbeat(self):
        if not self.alive:
            if self.server_alive:
                if hasattr(self, 'server'):
                    try:
                        self.server.stop()
                    except Exception:
                        pass
                self.server_alive = False
            else:
                if TORNADO5:
                    for callback in self.callbacks:
                        callback.stop()
                    self.ioloop.stop()
                else:
                    if not self.ioloop._callbacks:
                        self.ioloop.stop()

    def init_process(self):
        # IOLoop cannot survive a fork or be shared across processes
        # in any way. When multiple processes are being used, each process
        # should create its own IOLoop. We should clear current IOLoop
        # if exists before os.fork.
        IOLoop.clear_current()
        super().init_process()

    def run(self):
        self.ioloop = IOLoop.instance()
        self.alive = True
        self.server_alive = False

        if TORNADO5:
            self.callbacks = []
            self.callbacks.append(PeriodicCallback(self.watchdog, 1000))
            self.callbacks.append(PeriodicCallback(self.heartbeat, 1000))
            for callback in self.callbacks:
                callback.start()
        else:
            PeriodicCallback(self.watchdog, 1000, io_loop=self.ioloop).start()
            PeriodicCallback(self.heartbeat, 1000, io_loop=self.ioloop).start()

        # Assume the app is a WSGI callable if its not an
        # instance of tornado.web.Application or is an
        # instance of tornado.wsgi.WSGIApplication
        app = self.wsgi

        if tornado.version_info[0] < 6:
            if not isinstance(app, tornado.web.Application) or \
                    isinstance(app, tornado.wsgi.WSGIApplication):
                app = WSGIContainer(app)
        elif not isinstance(app, WSGIContainer) and \
                not isinstance(app, tornado.web.Application):
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
                    super().on_close(server_conn)

            server_class = _HTTPServer

        if self.cfg.is_ssl:
            if TORNADO5:
                server = server_class(app, ssl_options=ssl_context(self.cfg))
            else:
                server = server_class(app, io_loop=self.ioloop,
                                      ssl_options=ssl_context(self.cfg))
        else:
            if TORNADO5:
                server = server_class(app)
            else:
                server = server_class(app, io_loop=self.ioloop)

        self.server = server
        self.server_alive = True

        for s in self.sockets:
            s.setblocking(0)
            if hasattr(server, "add_socket"):  # tornado > 2.0
                server.add_socket(s)
            elif hasattr(server, "_sockets"):  # tornado 2.0
                server._sockets[s.fileno()] = s

        server.no_keep_alive = self.cfg.keepalive <= 0
        server.start(num_processes=1)

        self.ioloop.start()
