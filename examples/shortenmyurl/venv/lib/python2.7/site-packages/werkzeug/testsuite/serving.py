# -*- coding: utf-8 -*-
"""
    werkzeug.testsuite.serving
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Added serving tests.

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import sys
import time
try:
    import httplib
except ImportError:
    from http import client as httplib
try:
    from urllib2 import urlopen, HTTPError
except ImportError:  # pragma: no cover
    from urllib.request import urlopen
    from urllib.error import HTTPError

import unittest
from functools import update_wrapper

from werkzeug.testsuite import WerkzeugTestCase

from werkzeug import __version__ as version, serving
from werkzeug.testapp import test_app
from werkzeug._compat import StringIO
from threading import Thread



real_make_server = serving.make_server


def silencestderr(f):
    def new_func(*args, **kwargs):
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        try:
            return f(*args, **kwargs)
        finally:
            sys.stderr = old_stderr
    return update_wrapper(new_func, f)


def run_dev_server(application):
    servers = []

    def tracking_make_server(*args, **kwargs):
        srv = real_make_server(*args, **kwargs)
        servers.append(srv)
        return srv
    serving.make_server = tracking_make_server
    try:
        t = Thread(target=serving.run_simple,
                   args=('localhost', 0, application))
        t.setDaemon(True)
        t.start()
        time.sleep(0.25)
    finally:
        serving.make_server = real_make_server
    if not servers:
        return None, None
    server, = servers
    ip, port = server.socket.getsockname()[:2]
    if ':' in ip:
        ip = '[%s]' % ip
    return server, '%s:%d'  % (ip, port)


class ServingTestCase(WerkzeugTestCase):

    @silencestderr
    def test_serving(self):
        server, addr = run_dev_server(test_app)
        rv = urlopen('http://%s/?foo=bar&baz=blah' % addr).read()
        self.assert_in(b'WSGI Information', rv)
        self.assert_in(b'foo=bar&amp;baz=blah', rv)
        self.assert_in(b'Werkzeug/' + version.encode('ascii'), rv)

    @silencestderr
    def test_broken_app(self):
        def broken_app(environ, start_response):
            1 // 0
        server, addr = run_dev_server(broken_app)
        try:
            urlopen('http://%s/?foo=bar&baz=blah' % addr).read()
        except HTTPError as e:
            # In Python3 a 500 response causes an exception
            rv = e.read()
            assert b'Internal Server Error' in rv
        else:
            assert False, 'expected internal server error'

    @silencestderr
    def test_absolute_requests(self):
        def asserting_app(environ, start_response):
            assert environ['HTTP_HOST'] == 'surelynotexisting.example.com:1337'
            assert environ['PATH_INFO'] == '/index.htm'
            assert environ['SERVER_PORT'] == addr.split(':')[1]
            start_response('200 OK', [('Content-Type', 'text/html')])
            return [b'YES']

        server, addr = run_dev_server(asserting_app)
        conn = httplib.HTTPConnection(addr)
        conn.request('GET', 'http://surelynotexisting.example.com:1337/index.htm')
        res = conn.getresponse()
        assert res.read() == b'YES'


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ServingTestCase))
    return suite
