# -*- coding: utf-8 -
#
# This file is part of gunicorn released under the MIT license.
# See the NOTICE for more information.

from datetime import datetime
import os
import signal
import sys


from gunicorn import util
from gunicorn.workers.workertmp import WorkerTmp
from gunicorn.reloader import Reloader
from gunicorn.http.errors import InvalidHeader, InvalidHeaderName, \
InvalidRequestLine, InvalidRequestMethod, InvalidHTTPVersion, \
LimitRequestLine, LimitRequestHeaders
from gunicorn.http.errors import InvalidProxyLine, ForbiddenProxyRequest
from gunicorn.http.wsgi import default_environ, Response
from gunicorn.six import MAXSIZE


class Worker(object):

    SIGNALS = [getattr(signal, "SIG%s" % x) \
            for x in "ABRT HUP QUIT INT TERM USR1 USR2 WINCH CHLD".split()]

    PIPE = []

    def __init__(self, age, ppid, sockets, app, timeout, cfg, log):
        """\
        This is called pre-fork so it shouldn't do anything to the
        current process. If there's a need to make process wide
        changes you'll want to do that in ``self.init_process()``.
        """
        self.age = age
        self.ppid = ppid
        self.sockets = sockets
        self.app = app
        self.timeout = timeout
        self.cfg = cfg
        self.booted = False
        self.aborted = False

        self.nr = 0
        self.max_requests = cfg.max_requests or MAXSIZE
        self.alive = True
        self.log = log
        self.tmp = WorkerTmp(cfg)

    def __str__(self):
        return "<Worker %s>" % self.pid

    @property
    def pid(self):
        return os.getpid()

    def notify(self):
        """\
        Your worker subclass must arrange to have this method called
        once every ``self.timeout`` seconds. If you fail in accomplishing
        this task, the master process will murder your workers.
        """
        self.tmp.notify()

    def run(self):
        """\
        This is the mainloop of a worker process. You should override
        this method in a subclass to provide the intended behaviour
        for your particular evil schemes.
        """
        raise NotImplementedError()

    def init_process(self):
        """\
        If you override this method in a subclass, the last statement
        in the function should be to call this method with
        super(MyWorkerClass, self).init_process() so that the ``run()``
        loop is initiated.
        """

        # start the reloader
        if self.cfg.reload:
            def changed(fname):
                self.log.info("Worker reloading: %s modified", fname)
                os.kill(self.pid, signal.SIGQUIT)
                raise SystemExit()
            Reloader(callback=changed).start()

        # set environment' variables
        if self.cfg.env:
            for k, v in self.cfg.env.items():
                os.environ[k] = v

        util.set_owner_process(self.cfg.uid, self.cfg.gid)

        # Reseed the random number generator
        util.seed()

        # For waking ourselves up
        self.PIPE = os.pipe()
        for p in self.PIPE:
            util.set_non_blocking(p)
            util.close_on_exec(p)

        # Prevent fd inheritance
        [util.close_on_exec(s) for s in self.sockets]
        util.close_on_exec(self.tmp.fileno())

        self.log.close_on_exec()

        self.init_signals()

        self.wsgi = self.app.wsgi()

        self.cfg.post_worker_init(self)

        # Enter main run loop
        self.booted = True
        self.run()

    def init_signals(self):
        # reset signaling
        [signal.signal(s, signal.SIG_DFL) for s in self.SIGNALS]
        # init new signaling
        signal.signal(signal.SIGQUIT, self.handle_quit)
        signal.signal(signal.SIGTERM, self.handle_exit)
        signal.signal(signal.SIGINT, self.handle_quit)
        signal.signal(signal.SIGWINCH, self.handle_winch)
        signal.signal(signal.SIGUSR1, self.handle_usr1)
        signal.signal(signal.SIGABRT, self.handle_abort)

        # Don't let SIGTERM and SIGUSR1 disturb active requests
        # by interrupting system calls
        if hasattr(signal, 'siginterrupt'):  # python >= 2.6
            signal.siginterrupt(signal.SIGTERM, False)
            signal.siginterrupt(signal.SIGUSR1, False)

    def handle_usr1(self, sig, frame):
        self.log.reopen_files()

    def handle_exit(self, sig, frame):
        self.alive = False

    def handle_quit(self, sig, frame):
        self.alive = False
        # worker_int callback
        self.cfg.worker_int(self)
        sys.exit(0)

    def handle_abort(self, sig, frame):
        self.alive = False
        self.cfg.worker_abort(self)
        sys.exit(1)

    def handle_error(self, req, client, addr, exc):
        request_start = datetime.now()
        addr = addr or ('', -1)  # unix socket case
        if isinstance(exc, (InvalidRequestLine, InvalidRequestMethod,
            InvalidHTTPVersion, InvalidHeader, InvalidHeaderName,
            LimitRequestLine, LimitRequestHeaders,
            InvalidProxyLine, ForbiddenProxyRequest,)):

            status_int = 400
            reason = "Bad Request"

            if isinstance(exc, InvalidRequestLine):
                mesg = "Invalid Request Line '%s'" % str(exc)
            elif isinstance(exc, InvalidRequestMethod):
                mesg = "Invalid Method '%s'" % str(exc)
            elif isinstance(exc, InvalidHTTPVersion):
                mesg = "Invalid HTTP Version '%s'" % str(exc)
            elif isinstance(exc, (InvalidHeaderName, InvalidHeader,)):
                mesg = "%s" % str(exc)
                if not req and hasattr(exc, "req"):
                    req = exc.req  # for access log
            elif isinstance(exc, LimitRequestLine):
                mesg = "%s" % str(exc)
            elif isinstance(exc, LimitRequestHeaders):
                mesg = "Error parsing headers: '%s'" % str(exc)
            elif isinstance(exc, InvalidProxyLine):
                mesg = "'%s'" % str(exc)
            elif isinstance(exc, ForbiddenProxyRequest):
                reason = "Forbidden"
                mesg = "Request forbidden"
                status_int = 403

            self.log.debug("Invalid request from ip={ip}: {error}"\
                           "".format(ip=addr[0],
                                     error=str(exc),
                                    )
                          )
        else:
            self.log.exception("Error handling request")

            status_int = 500
            reason = "Internal Server Error"
            mesg = ""

        if req is not None:
            request_time = datetime.now() - request_start
            environ = default_environ(req, client, self.cfg)
            environ['REMOTE_ADDR'] = addr[0]
            environ['REMOTE_PORT'] = str(addr[1])
            resp = Response(req, client, self.cfg)
            resp.status = "%s %s" % (status_int, reason)
            resp.response_length = len(mesg)
            self.log.access(resp, req, environ, request_time)

        try:
            util.write_error(client, status_int, reason, mesg)
        except:
            self.log.debug("Failed to send error message.")

    def handle_winch(self, sig, fname):
        # Ignore SIGWINCH in worker. Fixes a crash on OpenBSD.
        return
