#
# This file is part of gunicorn released under the MIT license.
# See the NOTICE for more information.

from functools import partial
import sys

try:
    import eventlet
except ImportError:
    raise RuntimeError("eventlet worker requires eventlet 0.24.1 or higher")
else:
    from packaging.version import parse as parse_version
    if parse_version(eventlet.__version__) < parse_version('0.24.1'):
        raise RuntimeError("eventlet worker requires eventlet 0.24.1 or higher")

from eventlet import hubs, greenthread
from eventlet.greenio import GreenSocket
import eventlet.wsgi
import greenlet

from gunicorn.workers.base_async import AsyncWorker
from gunicorn.sock import ssl_wrap_socket

# ALREADY_HANDLED is removed in 0.30.3+ now it's `WSGI_LOCAL.already_handled: bool`
# https://github.com/eventlet/eventlet/pull/544
EVENTLET_WSGI_LOCAL = getattr(eventlet.wsgi, "WSGI_LOCAL", None)
EVENTLET_ALREADY_HANDLED = getattr(eventlet.wsgi, "ALREADY_HANDLED", None)


def _eventlet_socket_sendfile(self, file, offset=0, count=None):
    # Based on the implementation in gevent which in turn is slightly
    # modified from the standard library implementation.
    if self.gettimeout() == 0:
        raise ValueError("non-blocking sockets are not supported")
    if offset:
        file.seek(offset)
    blocksize = min(count, 8192) if count else 8192
    total_sent = 0
    # localize variable access to minimize overhead
    file_read = file.read
    sock_send = self.send
    try:
        while True:
            if count:
                blocksize = min(count - total_sent, blocksize)
                if blocksize <= 0:
                    break
            data = memoryview(file_read(blocksize))
            if not data:
                break  # EOF
            while True:
                try:
                    sent = sock_send(data)
                except BlockingIOError:
                    continue
                else:
                    total_sent += sent
                    if sent < len(data):
                        data = data[sent:]
                    else:
                        break
        return total_sent
    finally:
        if total_sent > 0 and hasattr(file, 'seek'):
            file.seek(offset + total_sent)


def _eventlet_serve(sock, handle, concurrency):
    """
    Serve requests forever.

    This code is nearly identical to ``eventlet.convenience.serve`` except
    that it attempts to join the pool at the end, which allows for gunicorn
    graceful shutdowns.
    """
    pool = eventlet.greenpool.GreenPool(concurrency)
    server_gt = eventlet.greenthread.getcurrent()

    while True:
        try:
            conn, addr = sock.accept()
            gt = pool.spawn(handle, conn, addr)
            gt.link(_eventlet_stop, server_gt, conn)
            conn, addr, gt = None, None, None
        except eventlet.StopServe:
            sock.close()
            pool.waitall()
            return


def _eventlet_stop(client, server, conn):
    """
    Stop a greenlet handling a request and close its connection.

    This code is lifted from eventlet so as not to depend on undocumented
    functions in the library.
    """
    try:
        try:
            client.wait()
        finally:
            conn.close()
    except greenlet.GreenletExit:
        pass
    except Exception:
        greenthread.kill(server, *sys.exc_info())


def patch_sendfile():
    # As of eventlet 0.25.1, GreenSocket.sendfile doesn't exist,
    # meaning the native implementations of socket.sendfile will be used.
    # If os.sendfile exists, it will attempt to use that, failing explicitly
    # if the socket is in non-blocking mode, which the underlying
    # socket object /is/. Even the regular _sendfile_use_send will
    # fail in that way; plus, it would use the underlying socket.send which isn't
    # properly cooperative. So we have to monkey-patch a working socket.sendfile()
    # into GreenSocket; in this method, `self.send` will be the GreenSocket's
    # send method which is properly cooperative.
    if not hasattr(GreenSocket, 'sendfile'):
        GreenSocket.sendfile = _eventlet_socket_sendfile


class EventletWorker(AsyncWorker):

    def patch(self):
        hubs.use_hub()
        eventlet.monkey_patch()
        patch_sendfile()

    def is_already_handled(self, respiter):
        # eventlet >= 0.30.3
        if getattr(EVENTLET_WSGI_LOCAL, "already_handled", None):
            raise StopIteration()
        # eventlet < 0.30.3
        if respiter == EVENTLET_ALREADY_HANDLED:
            raise StopIteration()
        return super().is_already_handled(respiter)

    def init_process(self):
        self.patch()
        super().init_process()

    def handle_quit(self, sig, frame):
        eventlet.spawn(super().handle_quit, sig, frame)

    def handle_usr1(self, sig, frame):
        eventlet.spawn(super().handle_usr1, sig, frame)

    def timeout_ctx(self):
        return eventlet.Timeout(self.cfg.keepalive or None, False)

    def handle(self, listener, client, addr):
        if self.cfg.is_ssl:
            client = ssl_wrap_socket(client, self.cfg)
        super().handle(listener, client, addr)

    def run(self):
        acceptors = []
        for sock in self.sockets:
            gsock = GreenSocket(sock)
            gsock.setblocking(1)
            hfun = partial(self.handle, gsock)
            acceptor = eventlet.spawn(_eventlet_serve, gsock, hfun,
                                      self.worker_connections)

            acceptors.append(acceptor)
            eventlet.sleep(0.0)

        while self.alive:
            self.notify()
            eventlet.sleep(1.0)

        self.notify()
        t = None
        try:
            with eventlet.Timeout(self.cfg.graceful_timeout) as t:
                for a in acceptors:
                    a.kill(eventlet.StopServe())
                for a in acceptors:
                    a.wait()
        except eventlet.Timeout as te:
            if te != t:
                raise
            for a in acceptors:
                a.kill()
