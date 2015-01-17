# -*- coding: utf-8 -*-
"""
    werkzeug.testsuite.internal
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Internal tests.

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import unittest

from datetime import datetime
from warnings import filterwarnings, resetwarnings

from werkzeug.testsuite import WerkzeugTestCase
from werkzeug.wrappers import Request, Response

from werkzeug import _internal as internal
from werkzeug.test import create_environ


class InternalTestCase(WerkzeugTestCase):

    def test_date_to_unix(self):
        assert internal._date_to_unix(datetime(1970, 1, 1)) == 0
        assert internal._date_to_unix(datetime(1970, 1, 1, 1, 0, 0)) == 3600
        assert internal._date_to_unix(datetime(1970, 1, 1, 1, 1, 1)) == 3661
        x = datetime(2010, 2, 15, 16, 15, 39)
        assert internal._date_to_unix(x) == 1266250539

    def test_easteregg(self):
        req = Request.from_values('/?macgybarchakku')
        resp = Response.force_type(internal._easteregg(None), req)
        assert b'About Werkzeug' in resp.get_data()
        assert b'the Swiss Army knife of Python web development' in resp.get_data()

    def test_wrapper_internals(self):
        req = Request.from_values(data={'foo': 'bar'}, method='POST')
        req._load_form_data()
        assert req.form.to_dict() == {'foo': 'bar'}

        # second call does not break
        req._load_form_data()
        assert req.form.to_dict() == {'foo': 'bar'}

        # check reprs
        assert repr(req) == "<Request 'http://localhost/' [POST]>"
        resp = Response()
        assert repr(resp) == '<Response 0 bytes [200 OK]>'
        resp.set_data('Hello World!')
        assert repr(resp) == '<Response 12 bytes [200 OK]>'
        resp.response = iter(['Test'])
        assert repr(resp) == '<Response streamed [200 OK]>'

        # unicode data does not set content length
        response = Response([u'Hällo Wörld'])
        headers = response.get_wsgi_headers(create_environ())
        assert u'Content-Length' not in headers

        response = Response([u'Hällo Wörld'.encode('utf-8')])
        headers = response.get_wsgi_headers(create_environ())
        assert u'Content-Length' in headers

        # check for internal warnings
        filterwarnings('error', category=Warning)
        response = Response()
        environ = create_environ()
        response.response = 'What the...?'
        self.assert_raises(Warning, lambda: list(response.iter_encoded()))
        self.assert_raises(Warning, lambda: list(response.get_app_iter(environ)))
        response.direct_passthrough = True
        self.assert_raises(Warning, lambda: list(response.iter_encoded()))
        self.assert_raises(Warning, lambda: list(response.get_app_iter(environ)))
        resetwarnings()


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(InternalTestCase))
    return suite
