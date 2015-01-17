# -*- coding: utf-8 -*-
"""
    werkzeug.testsuite.contrib.wrappers
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Added tests for the sessions.

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import with_statement

import unittest

from werkzeug.testsuite import WerkzeugTestCase

from werkzeug.contrib import wrappers
from werkzeug import routing
from werkzeug.wrappers import Request, Response


class WrappersTestCase(WerkzeugTestCase):

    def test_reverse_slash_behavior(self):
        class MyRequest(wrappers.ReverseSlashBehaviorRequestMixin, Request):
            pass
        req = MyRequest.from_values('/foo/bar', 'http://example.com/test')
        assert req.url == 'http://example.com/test/foo/bar'
        assert req.path == 'foo/bar'
        assert req.script_root == '/test/'

        # make sure the routing system works with the slashes in
        # reverse order as well.
        map = routing.Map([routing.Rule('/foo/bar', endpoint='foo')])
        adapter = map.bind_to_environ(req.environ)
        assert adapter.match() == ('foo', {})
        adapter = map.bind(req.host, req.script_root)
        assert adapter.match(req.path) == ('foo', {})

    def test_dynamic_charset_request_mixin(self):
        class MyRequest(wrappers.DynamicCharsetRequestMixin, Request):
            pass
        env = {'CONTENT_TYPE': 'text/html'}
        req = MyRequest(env)
        assert req.charset == 'latin1'

        env = {'CONTENT_TYPE': 'text/html; charset=utf-8'}
        req = MyRequest(env)
        assert req.charset == 'utf-8'

        env = {'CONTENT_TYPE': 'application/octet-stream'}
        req = MyRequest(env)
        assert req.charset == 'latin1'
        assert req.url_charset == 'latin1'

        MyRequest.url_charset = 'utf-8'
        env = {'CONTENT_TYPE': 'application/octet-stream'}
        req = MyRequest(env)
        assert req.charset == 'latin1'
        assert req.url_charset == 'utf-8'

        def return_ascii(x):
            return "ascii"
        env = {'CONTENT_TYPE': 'text/plain; charset=x-weird-charset'}
        req = MyRequest(env)
        req.unknown_charset = return_ascii
        assert req.charset == 'ascii'
        assert req.url_charset == 'utf-8'

    def test_dynamic_charset_response_mixin(self):
        class MyResponse(wrappers.DynamicCharsetResponseMixin, Response):
            default_charset = 'utf-7'
        resp = MyResponse(mimetype='text/html')
        assert resp.charset == 'utf-7'
        resp.charset = 'utf-8'
        assert resp.charset == 'utf-8'
        assert resp.mimetype == 'text/html'
        assert resp.mimetype_params == {'charset': 'utf-8'}
        resp.mimetype_params['charset'] = 'iso-8859-15'
        assert resp.charset == 'iso-8859-15'
        resp.set_data(u'Hällo Wörld')
        assert b''.join(resp.iter_encoded()) == \
               u'Hällo Wörld'.encode('iso-8859-15')
        del resp.headers['content-type']
        try:
            resp.charset = 'utf-8'
        except TypeError as e:
            pass
        else:
            assert False, 'expected type error on charset setting without ct'


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(WrappersTestCase))
    return suite
