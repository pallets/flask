# -*- coding: utf-8 -
#
# This file is part of gunicorn released under the MIT license.
# See the NOTICE for more information.

import errno
import os
import socket
import stat
import sys
import time

from gunicorn import util
from gunicorn.six import string_types

SD_LISTEN_FDS_START = 3


class BaseSocket(object):

    def __init__(self, address, conf, log, fd=None):
        self.log = log
        self.conf = conf

        self.cfg_addr = address
        if fd is None:
            sock = socket.socket(self.FAMILY, socket.SOCK_STREAM)
        else:
            sock = socket.fromfd(fd, self.FAMILY, socket.SOCK_STREAM)

        self.sock = self.set_options(sock, bound=(fd is not None))

    def __str__(self, name):
        return "<socket %d>" % self.sock.fileno()

    def __getattr__(self, name):
        return getattr(self.sock, name)

    def set_options(self, sock, bound=False):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if not bound:
            self.bind(sock)
        sock.setblocking(0)
        sock.listen(self.conf.backlog)
        return sock

    def bind(self, sock):
        sock.bind(self.cfg_addr)

    def close(self):
        try:
            self.sock.close()
        except socket.error as e:
            self.log.info("Error while closing socket %s", str(e))
        time.sleep(0.3)
        del self.sock


class TCPSocket(BaseSocket):

    FAMILY = socket.AF_INET

    def __str__(self):
        if self.conf.is_ssl:
            scheme = "https"
        else:
            scheme = "http"

        addr = self.sock.getsockname()
        return "%s://%s:%d" % (scheme, addr[0], addr[1])

    def set_options(self, sock, bound=False):
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        return super(TCPSocket, self).set_options(sock, bound=bound)


class TCP6Socket(TCPSocket):

    FAMILY = socket.AF_INET6

    def __str__(self):
        (host, port, fl, sc) = self.sock.getsockname()
        return "http://[%s]:%d" % (host, port)


class UnixSocket(BaseSocket):

    FAMILY = socket.AF_UNIX

    def __init__(self, addr, conf, log, fd=None):
        if fd is None:
            try:
                st = os.stat(addr)
            except OSError as e:
                if e.args[0] != errno.ENOENT:
                    raise
            else:
                if stat.S_ISSOCK(st.st_mode):
                    os.remove(addr)
                else:
                    raise ValueError("%r is not a socket" % addr)
        super(UnixSocket, self).__init__(addr, conf, log, fd=fd)

    def __str__(self):
        return "unix:%s" % self.cfg_addr

    def bind(self, sock):
        old_umask = os.umask(self.conf.umask)
        sock.bind(self.cfg_addr)
        util.chown(self.cfg_addr, self.conf.uid, self.conf.gid)
        os.umask(old_umask)

    def close(self):
        super(UnixSocket, self).close()
        os.unlink(self.cfg_addr)


def _sock_type(addr):
    if isinstance(addr, tuple):
        if util.is_ipv6(addr[0]):
            sock_type = TCP6Socket
        else:
            sock_type = TCPSocket
    elif isinstance(addr, string_types):
        sock_type = UnixSocket
    else:
        raise TypeError("Unable to create socket from: %r" % addr)
    return sock_type


def create_sockets(conf, log):
    """
    Create a new socket for the given address. If the
    address is a tuple, a TCP socket is created. If it
    is a string, a Unix socket is created. Otherwise
    a TypeError is raised.
    """

    # Systemd support, use the sockets managed by systemd and passed to
    # gunicorn.
    # http://www.freedesktop.org/software/systemd/man/systemd.socket.html
    listeners = []
    if ('LISTEN_PID' in os.environ
            and int(os.environ.get('LISTEN_PID')) == os.getpid()):
        for i in range(int(os.environ.get('LISTEN_FDS', 0))):
            fd = i + SD_LISTEN_FDS_START
            try:
                sock = socket.fromfd(fd, socket.AF_UNIX, socket.SOCK_STREAM)
                sockname = sock.getsockname()
                if isinstance(sockname, str) and sockname.startswith('/'):
                    listeners.append(UnixSocket(sockname, conf, log, fd=fd))
                elif len(sockname) == 2 and '.' in sockname[0]:
                    listeners.append(TCPSocket("%s:%s" % sockname, conf, log,
                        fd=fd))
                elif len(sockname) == 4 and ':' in sockname[0]:
                    listeners.append(TCP6Socket("[%s]:%s" % sockname[:2], conf,
                        log, fd=fd))
            except socket.error:
                pass
        del os.environ['LISTEN_PID'], os.environ['LISTEN_FDS']

        if listeners:
            log.debug('Socket activation sockets: %s',
                    ",".join([str(l) for l in listeners]))
            return listeners

    # get it only once
    laddr = conf.address

    # check ssl config early to raise the error on startup
    # only the certfile is needed since it can contains the keyfile
    if conf.certfile and not os.path.exists(conf.certfile):
        raise ValueError('certfile "%s" does not exist' % conf.certfile)

    if conf.keyfile and not os.path.exists(conf.keyfile):
        raise ValueError('keyfile "%s" does not exist' % conf.keyfile)

    # sockets are already bound
    if 'GUNICORN_FD' in os.environ:
        fds = os.environ.pop('GUNICORN_FD').split(',')
        for i, fd in enumerate(fds):
            fd = int(fd)
            addr = laddr[i]
            sock_type = _sock_type(addr)

            try:
                listeners.append(sock_type(addr, conf, log, fd=fd))
            except socket.error as e:
                if e.args[0] == errno.ENOTCONN:
                    log.error("GUNICORN_FD should refer to an open socket.")
                else:
                    raise
        return listeners

    # no sockets is bound, first initialization of gunicorn in this env.
    for addr in laddr:
        sock_type = _sock_type(addr)

        # If we fail to create a socket from GUNICORN_FD
        # we fall through and try and open the socket
        # normally.
        sock = None
        for i in range(5):
            try:
                sock = sock_type(addr, conf, log)
            except socket.error as e:
                if e.args[0] == errno.EADDRINUSE:
                    log.error("Connection in use: %s", str(addr))
                if e.args[0] == errno.EADDRNOTAVAIL:
                    log.error("Invalid address: %s", str(addr))
                    sys.exit(1)
                if i < 5:
                    log.error("Retrying in 1 second.")
                    time.sleep(1)
            else:
                break

        if sock is None:
            log.error("Can't connect to %s", str(addr))
            sys.exit(1)

        listeners.append(sock)

    return listeners
