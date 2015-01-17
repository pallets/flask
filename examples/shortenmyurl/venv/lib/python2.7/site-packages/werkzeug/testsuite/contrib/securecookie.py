# -*- coding: utf-8 -*-
"""
    werkzeug.testsuite.securecookie
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests the secure cookie.

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import unittest

from werkzeug.testsuite import WerkzeugTestCase

from werkzeug.utils import parse_cookie
from werkzeug.wrappers import Request, Response
from werkzeug.contrib.securecookie import SecureCookie


class SecureCookieTestCase(WerkzeugTestCase):

    def test_basic_support(self):
        c = SecureCookie(secret_key=b'foo')
        assert c.new
        assert not c.modified
        assert not c.should_save
        c['x'] = 42
        assert c.modified
        assert c.should_save
        s = c.serialize()

        c2 = SecureCookie.unserialize(s, b'foo')
        assert c is not c2
        assert not c2.new
        assert not c2.modified
        assert not c2.should_save
        self.assert_equal(c2, c)

        c3 = SecureCookie.unserialize(s, b'wrong foo')
        assert not c3.modified
        assert not c3.new
        self.assert_equal(c3, {})

    def test_wrapper_support(self):
        req = Request.from_values()
        resp = Response()
        c = SecureCookie.load_cookie(req, secret_key=b'foo')
        assert c.new
        c['foo'] = 42
        self.assert_equal(c.secret_key, b'foo')
        c.save_cookie(resp)

        req = Request.from_values(headers={
            'Cookie':  'session="%s"' % parse_cookie(resp.headers['set-cookie'])['session']
        })
        c2 = SecureCookie.load_cookie(req, secret_key=b'foo')
        assert not c2.new
        self.assert_equal(c2, c)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SecureCookieTestCase))
    return suite
