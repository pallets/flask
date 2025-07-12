#
# This file is part of gunicorn released under the MIT license.
# See the NOTICE for more information.

import os
import sys
from datetime import datetime
from functools import partial
import time

try:
    import gevent
except ImportError:
    raise RuntimeError("gevent worker requires gevent 1.4 or higher")
else:
    from packaging.version import parse as parse_version
    if parse_version(gevent.__version__) < parse_version('1.4'):
        raise RuntimeError("gevent worker requires gevent 1.4 or higher")

from gevent.pool import Pool
from gevent.server import StreamServer
from gevent import hub, monkey, socket, pywsgi

import gunicorn
from gunicorn.http.wsgi import base_environ
from gunicorn.sock import ssl_context
from gunicorn.workers.base_async import AsyncWorker

VERSION = "gevent/%s gunicorn/%s" % (gevent.__version__, gunicorn.__version__)


class GeventWorker(AsyncWorker):

    server_class = None
    wsgi_handler = None

    def patch(self):
        monkey.patch_all()

        # patch sockets
        sockets = []
        for s in self.sockets:
            sockets.append(socket.socket(s.FAMILY, socket.SOCK_STREAM,
                                         fileno=s.sock.fileno()))
        self.sockets = sockets

    def notify(self):
        super().notify()
        if self.ppid != os.getppid():
            self.log.info("Parent changed, shutting down: %s", self)
            sys.exit(0)

    def timeout_ctx(self):
        return gevent.Timeout(self.cfg.keepalive, False)

    def run(self):
        servers = []
        ssl_args = {}

        if self.cfg.is_ssl:
            ssl_args = {"ssl_context": ssl_context(self.cfg)}

        for s in self.sockets:
            s.setblocking(1)
            pool = Pool(self.worker_connections)
            if self.server_class is not None:
                environ = base_environ(self.cfg)
                environ.update({
                    "wsgi.multithread": True,
                    "SERVER_SOFTWARE": VERSION,
                })
                server = self.server_class(
                    s, application=self.wsgi, spawn=pool, log=self.log,
                    handler_class=self.wsgi_handler, environ=environ,
                    **ssl_args)
            else:
                hfun = partial(self.handle, s)
                server = StreamServer(s, handle=hfun, spawn=pool, **ssl_args)
                if self.cfg.workers > 1:
                    server.max_accept = 1

            server.start()
            servers.append(server)

        while self.alive:
            self.notify()
            gevent.sleep(1.0)

        try:
            # Stop accepting requests
            for server in servers:
                if hasattr(server, 'close'):  # gevent 1.0
                    server.close()
                if hasattr(server, 'kill'):  # gevent < 1.0
                    server.kill()

            # Handle current requests until graceful_timeout
            ts = time.time()
            while time.time() - ts <= self.cfg.graceful_timeout:
                accepting = 0
                for server in servers:
                    if server.pool.free_count() != server.pool.size:
                        accepting += 1

                # if no server is accepting a connection, we can exit
                if not accepting:
                    return

                self.notify()
                gevent.sleep(1.0)

            # Force kill all active the handlers
            self.log.warning("Worker graceful timeout (pid:%s)", self.pid)
            for server in servers:
                server.stop(timeout=1)
        except Exception:
            pass

    def handle(self, listener, client, addr):
        # Connected socket timeout defaults to socket.getdefaulttimeout().
        # This forces to blocking mode.
        client.setblocking(1)
        super().handle(listener, client, addr)

    def handle_request(self, listener_name, req, sock, addr):
        try:
            super().handle_request(listener_name, req, sock, addr)
        except gevent.GreenletExit:
            pass
        except SystemExit:
            pass

    def handle_quit(self, sig, frame):
        # Move this out of the signal handler so we can use
        # blocking calls. See #1126
        gevent.spawn(super().handle_quit, sig, frame)

    def handle_usr1(self, sig, frame):
        # Make the gevent workers handle the usr1 signal
        # by deferring to a new greenlet. See #1645
        gevent.spawn(super().handle_usr1, sig, frame)

    def init_process(self):
        self.patch()
        hub.reinit()
        super().init_process()


class GeventResponse:

    status = None
    headers = None
    sent = None

    def __init__(self, status, headers, clength):
        self.status = status
        self.headers = headers
        self.sent = clength


class PyWSGIHandler(pywsgi.WSGIHandler):

    def log_request(self):
        start = datetime.fromtimestamp(self.time_start)
        finish = datetime.fromtimestamp(self.time_finish)
        response_time = finish - start
        resp_headers = getattr(self, 'response_headers', {})

        # Status is expected to be a string but is encoded to bytes in gevent for PY3
        # Except when it isn't because gevent uses hardcoded strings for network errors.
        status = self.status.decode() if isinstance(self.status, bytes) else self.status
        resp = GeventResponse(status, resp_headers, self.response_length)
        if hasattr(self, 'headers'):
            req_headers = self.headers.items()
        else:
            req_headers = []
        self.server.log.access(resp, req_headers, self.environ, response_time)

    def get_environ(self):
        env = super().get_environ()
        env['gunicorn.sock'] = self.socket
        env['RAW_URI'] = self.path
        return env


class PyWSGIServer(pywsgi.WSGIServer):
    pass


class GeventPyWSGIWorker(GeventWorker):
    "The Gevent StreamServer based workers."
    server_class = PyWSGIServer
    wsgi_handler = PyWSGIHandler
