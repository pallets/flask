# -*- coding: utf-8 -*-
"""
    werkzeug.testsuite.exceptions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The tests for the exception classes.

    TODO:

    -   This is undertested.  HTML is never checked

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import unittest

from werkzeug.testsuite import WerkzeugTestCase

from werkzeug import exceptions
from werkzeug.wrappers import Response
from werkzeug._compat import text_type


class ExceptionsTestCase(WerkzeugTestCase):

    def test_proxy_exception(self):
        orig_resp = Response('Hello World')
        try:
            exceptions.abort(orig_resp)
        except exceptions.HTTPException as e:
            resp = e.get_response({})
        else:
            self.fail('exception not raised')
        self.assert_true(resp is orig_resp)
        self.assert_equal(resp.get_data(), b'Hello World')

    def test_aborter(self):
        abort = exceptions.abort
        self.assert_raises(exceptions.BadRequest, abort, 400)
        self.assert_raises(exceptions.Unauthorized, abort, 401)
        self.assert_raises(exceptions.Forbidden, abort, 403)
        self.assert_raises(exceptions.NotFound, abort, 404)
        self.assert_raises(exceptions.MethodNotAllowed, abort, 405, ['GET', 'HEAD'])
        self.assert_raises(exceptions.NotAcceptable, abort, 406)
        self.assert_raises(exceptions.RequestTimeout, abort, 408)
        self.assert_raises(exceptions.Gone, abort, 410)
        self.assert_raises(exceptions.LengthRequired, abort, 411)
        self.assert_raises(exceptions.PreconditionFailed, abort, 412)
        self.assert_raises(exceptions.RequestEntityTooLarge, abort, 413)
        self.assert_raises(exceptions.RequestURITooLarge, abort, 414)
        self.assert_raises(exceptions.UnsupportedMediaType, abort, 415)
        self.assert_raises(exceptions.UnprocessableEntity, abort, 422)
        self.assert_raises(exceptions.InternalServerError, abort, 500)
        self.assert_raises(exceptions.NotImplemented, abort, 501)
        self.assert_raises(exceptions.BadGateway, abort, 502)
        self.assert_raises(exceptions.ServiceUnavailable, abort, 503)

        myabort = exceptions.Aborter({1: exceptions.NotFound})
        self.assert_raises(LookupError, myabort, 404)
        self.assert_raises(exceptions.NotFound, myabort, 1)

        myabort = exceptions.Aborter(extra={1: exceptions.NotFound})
        self.assert_raises(exceptions.NotFound, myabort, 404)
        self.assert_raises(exceptions.NotFound, myabort, 1)

    def test_exception_repr(self):
        exc = exceptions.NotFound()
        self.assert_equal(text_type(exc), '404: Not Found')
        self.assert_equal(repr(exc), "<NotFound '404: Not Found'>")

        exc = exceptions.NotFound('Not There')
        self.assert_equal(text_type(exc), '404: Not Found')
        self.assert_equal(repr(exc), "<NotFound '404: Not Found'>")

    def test_special_exceptions(self):
        exc = exceptions.MethodNotAllowed(['GET', 'HEAD', 'POST'])
        h = dict(exc.get_headers({}))
        self.assert_equal(h['Allow'], 'GET, HEAD, POST')
        self.assert_true('The method is not allowed' in exc.get_description())


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ExceptionsTestCase))
    return suite
