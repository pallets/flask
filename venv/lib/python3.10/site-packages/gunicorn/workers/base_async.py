#
# This file is part of gunicorn released under the MIT license.
# See the NOTICE for more information.

from datetime import datetime
import errno
import socket
import ssl
import sys

from gunicorn import http
from gunicorn.http import wsgi
from gunicorn import util
from gunicorn.workers import base

ALREADY_HANDLED = object()


class AsyncWorker(base.Worker):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.worker_connections = self.cfg.worker_connections

    def timeout_ctx(self):
        raise NotImplementedError()

    def is_already_handled(self, respiter):
        # some workers will need to overload this function to raise a StopIteration
        return respiter == ALREADY_HANDLED

    def handle(self, listener, client, addr):
        req = None
        try:
            parser = http.RequestParser(self.cfg, client, addr)
            try:
                listener_name = listener.getsockname()
                if not self.cfg.keepalive:
                    req = next(parser)
                    self.handle_request(listener_name, req, client, addr)
                else:
                    # keepalive loop
                    proxy_protocol_info = {}
                    while True:
                        req = None
                        with self.timeout_ctx():
                            req = next(parser)
                        if not req:
                            break
                        if req.proxy_protocol_info:
                            proxy_protocol_info = req.proxy_protocol_info
                        else:
                            req.proxy_protocol_info = proxy_protocol_info
                        self.handle_request(listener_name, req, client, addr)
            except http.errors.NoMoreData as e:
                self.log.debug("Ignored premature client disconnection. %s", e)
            except StopIteration as e:
                self.log.debug("Closing connection. %s", e)
            except ssl.SSLError:
                # pass to next try-except level
                util.reraise(*sys.exc_info())
            except OSError:
                # pass to next try-except level
                util.reraise(*sys.exc_info())
            except Exception as e:
                self.handle_error(req, client, addr, e)
        except ssl.SSLError as e:
            if e.args[0] == ssl.SSL_ERROR_EOF:
                self.log.debug("ssl connection closed")
                client.close()
            else:
                self.log.debug("Error processing SSL request.")
                self.handle_error(req, client, addr, e)
        except OSError as e:
            if e.errno not in (errno.EPIPE, errno.ECONNRESET, errno.ENOTCONN):
                self.log.exception("Socket error processing request.")
            else:
                if e.errno == errno.ECONNRESET:
                    self.log.debug("Ignoring connection reset")
                elif e.errno == errno.ENOTCONN:
                    self.log.debug("Ignoring socket not connected")
                else:
                    self.log.debug("Ignoring EPIPE")
        except BaseException as e:
            self.handle_error(req, client, addr, e)
        finally:
            util.close(client)

    def handle_request(self, listener_name, req, sock, addr):
        request_start = datetime.now()
        environ = {}
        resp = None
        try:
            self.cfg.pre_request(self, req)
            resp, environ = wsgi.create(req, sock, addr,
                                        listener_name, self.cfg)
            environ["wsgi.multithread"] = True
            self.nr += 1
            if self.nr >= self.max_requests:
                if self.alive:
                    self.log.info("Autorestarting worker after current request.")
                    self.alive = False

            if not self.alive or not self.cfg.keepalive:
                resp.force_close()

            respiter = self.wsgi(environ, resp.start_response)
            if self.is_already_handled(respiter):
                return False
            try:
                if isinstance(respiter, environ['wsgi.file_wrapper']):
                    resp.write_file(respiter)
                else:
                    for item in respiter:
                        resp.write(item)
                resp.close()
            finally:
                request_time = datetime.now() - request_start
                self.log.access(resp, req, environ, request_time)
                if hasattr(respiter, "close"):
                    respiter.close()
            if resp.should_close():
                raise StopIteration()
        except StopIteration:
            raise
        except OSError:
            # If the original exception was a socket.error we delegate
            # handling it to the caller (where handle() might ignore it)
            util.reraise(*sys.exc_info())
        except Exception:
            if resp and resp.headers_sent:
                # If the requests have already been sent, we should close the
                # connection to indicate the error.
                self.log.exception("Error handling request")
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                    sock.close()
                except OSError:
                    pass
                raise StopIteration()
            raise
        finally:
            try:
                self.cfg.post_request(self, req, environ, resp)
            except Exception:
                self.log.exception("Exception in post_request hook")
        return True
