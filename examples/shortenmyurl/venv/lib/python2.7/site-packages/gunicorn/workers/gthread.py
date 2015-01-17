# -*- coding: utf-8 -
#
# This file is part of gunicorn released under the MIT license.
# See the NOTICE for more information.

# design:
# a threaded worker accepts connections in the main loop, accepted
# connections are are added to the thread pool as a connection job. On
# keepalive connections are put back in the loop waiting for an event.
# If no event happen after the keep alive timeout, the connectoin is
# closed.

from collections import deque
from datetime import datetime
import errno
from functools import partial
import os
import operator
import socket
import ssl
import sys
import time

from .. import http
from ..http import wsgi
from .. import util
from . import base
from .. import six


try:
    import concurrent.futures as futures
except ImportError:
    raise RuntimeError("""
    You need 'concurrent' installed to use this worker with this python
    version.
    """)

try:
    from asyncio import selectors
except ImportError:
    try:
        from trollius import selectors
    except ImportError:
        raise RuntimeError("""
        You need 'trollius' installed to use this worker with this python
        version.
        """)


class TConn(object):

    def __init__(self, cfg, listener, sock, addr):
        self.cfg = cfg
        self.listener = listener
        self.sock = sock
        self.addr = addr

        self.timeout = None
        self.parser = None

        # set the socket to non blocking
        self.sock.setblocking(False)

    def init(self):
        self.sock.setblocking(True)
        if self.parser is None:
            # wrap the socket if needed
            if self.cfg.is_ssl:
                self.sock = ssl.wrap_socket(client, server_side=True,
                        **self.cfg.ssl_options)


            # initialize the parser
            self.parser = http.RequestParser(self.cfg, self.sock)
            return True
        return False

    def set_timeout(self):
        # set the timeout
        self.timeout = time.time() + self.cfg.keepalive

    def __lt__(self, other):
        return self.timeout < other.timeout

    __cmp__ = __lt__


class ThreadWorker(base.Worker):

    def __init__(self, *args, **kwargs):
        super(ThreadWorker, self).__init__(*args, **kwargs)
        self.worker_connections = self.cfg.worker_connections

        # initialise the pool
        self.tpool = None
        self.poller = None
        self.futures = deque()
        self._keep = deque()

    def _wrap_future(self, fs, conn):
        fs.conn = conn
        self.futures.append(fs)
        fs.add_done_callback(self.finish_request)

    def init_process(self):
        self.tpool = futures.ThreadPoolExecutor(max_workers=self.cfg.threads)
        self.poller = selectors.DefaultSelector()
        super(ThreadWorker, self).init_process()

    def accept(self, listener):
        try:
            client, addr = listener.accept()
            conn = TConn(self.cfg, listener, client, addr)

            # wait for the read event to handle the connection
            self.poller.register(client, selectors.EVENT_READ,
                    partial(self.handle_client, conn))

        except socket.error as e:
            if e.args[0] not in (errno.EAGAIN,
                    errno.ECONNABORTED, errno.EWOULDBLOCK):
                raise

    def handle_client(self, conn, client):
        # unregister the client from the poller
        self.poller.unregister(client)

        # submit the connection to a worker
        fs = self.tpool.submit(self.handle, conn)
        self._wrap_future(fs, conn)

    def murder_keepalived(self):
        now = time.time()
        while True:
            try:
                # remove the connection from the queue
                conn = self._keep.popleft()
            except IndexError:
                break

            delta = conn.timeout - now
            if delta > 0:
                # add the connection back to the queue
                self._keep.appendleft(conn)
                break
            else:
                # remove the socket from the poller
                self.poller.unregister(conn.sock)

                # close the socket
                util.close(conn.sock)

    def run(self):
        # init listeners, add them to the event loop
        for s in self.sockets:
            s.setblocking(False)
            self.poller.register(s, selectors.EVENT_READ, self.accept)

        timeout = self.cfg.timeout or 0.5

        while self.alive:
            # If our parent changed then we shut down.
            if self.ppid != os.getppid():
                self.log.info("Parent changed, shutting down: %s", self)
                return

            # notify the arbiter we are alive
            self.notify()

            events = self.poller.select(0.2)
            for key, mask in events:
                callback = key.data
                callback(key.fileobj)

            # hanle keepalive timeouts
            self.murder_keepalived()

            # if we more connections than the max number of connections
            # accepted on a worker, wait until some complete or exit.
            if len(self.futures) >= self.worker_connections:
                res = futures.wait(self.futures, timeout=timeout)
                if not res:
                    self.log.info("max requests achieved")
                    break

        # shutdown the pool
        self.poller.close()
        self.tpool.shutdown(False)

        # wait for the workers
        futures.wait(self.futures, timeout=self.cfg.graceful_timeout)

        # if we have still fures running, try to close them
        while True:
            try:
                fs = self.futures.popleft()
            except IndexError:
                break

            sock = fs.conn.sock

            # the future is not running, cancel it
            if not fs.done() and not fs.running():
                fs.cancel()

            # make sure we close the sockets after the graceful timeout
            util.close(sock)

    def finish_request(self, fs):
        try:
            (keepalive, conn) = fs.result()
            # if the connection should be kept alived add it
            # to the eventloop and record it
            if keepalive:
                # flag the socket as non blocked
                conn.sock.setblocking(False)

                # register the connection
                conn.set_timeout()
                self._keep.append(conn)

                # add the socket to the event loop
                self.poller.register(conn.sock, selectors.EVENT_READ,
                        partial(self.handle_client, conn))
            else:
                util.close(conn.sock)
        except:
            # an exception happened, make sure to close the
            # socket.
            util.close(fs.conn.sock)
        finally:
            # remove the future from our list
            try:
                self.futures.remove(fs)
            except ValueError:
                pass

    def handle(self, conn):
        if not conn.init():
            # connection kept alive
            try:
                self._keep.remove(conn)
            except ValueError:
                pass

        keepalive = False
        req = None
        try:
            req = six.next(conn.parser)
            if not req:
                return (False, conn)

            # handle the request
            keepalive = self.handle_request(req, conn)
            if keepalive:
                return (keepalive, conn)
        except http.errors.NoMoreData as e:
            self.log.debug("Ignored premature client disconnection. %s", e)

        except StopIteration as e:
            self.log.debug("Closing connection. %s", e)
        except ssl.SSLError as e:
            if e.args[0] == ssl.SSL_ERROR_EOF:
                self.log.debug("ssl connection closed")
                conn.sock.close()
            else:
                self.log.debug("Error processing SSL request.")
                self.handle_error(req, conn.sock, conn.addr, e)

        except socket.error as e:
            if e.args[0] not in (errno.EPIPE, errno.ECONNRESET):
                self.log.exception("Socket error processing request.")
            else:
                if e.args[0] == errno.ECONNRESET:
                    self.log.debug("Ignoring connection reset")
                else:
                    self.log.debug("Ignoring connection epipe")
        except Exception as e:
            self.handle_error(req, conn.sock, conn.addr, e)

        return (False, conn)

    def handle_request(self, req, conn):
        environ = {}
        resp = None
        try:
            self.cfg.pre_request(self, req)
            request_start = datetime.now()
            resp, environ = wsgi.create(req, conn.sock, conn.addr,
                    conn.listener.getsockname(), self.cfg)
            environ["wsgi.multithread"] = True

            self.nr += 1

            if self.alive and self.nr >= self.max_requests:
                self.log.info("Autorestarting worker after current request.")
                resp.force_close()
                self.alive = False

            if not self.cfg.keepalive:
                resp.force_close()

            respiter = self.wsgi(environ, resp.start_response)
            try:
                if isinstance(respiter, environ['wsgi.file_wrapper']):
                    resp.write_file(respiter)
                else:
                    for item in respiter:
                        resp.write(item)

                resp.close()
                request_time = datetime.now() - request_start
                self.log.access(resp, req, environ, request_time)
            finally:
                if hasattr(respiter, "close"):
                    respiter.close()

            if resp.should_close():
                self.log.debug("Closing connection.")
                return False
        except socket.error:
            exc_info = sys.exc_info()
            # pass to next try-except level
            six.reraise(exc_info[0], exc_info[1], exc_info[2])
        except Exception:
            if resp and resp.headers_sent:
                # If the requests have already been sent, we should close the
                # connection to indicate the error.
                self.log.exception("Error handling request")
                try:
                    conn.sock.shutdown(socket.SHUT_RDWR)
                    conn.sock.close()
                except socket.error:
                    pass
                raise StopIteration()
            raise
        finally:
            try:
                self.cfg.post_request(self, req, environ, resp)
            except Exception:
                self.log.exception("Exception in post_request hook")

        return True
