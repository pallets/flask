# -*- coding: utf-8 -*-
"""
    tests.subclassing
    ~~~~~~~~~~~~~~~~~

    Test that certain behavior of flask can be customized by
    subclasses.

    :copyright: 2010 Pallets
    :license: BSD-3-Clause
"""

import flask

from flask._compat import StringIO


def test_suppressed_exception_logging():
    class SuppressedFlask(flask.Flask):
        def log_exception(self, exc_info):
            pass

    out = StringIO()
    app = SuppressedFlask(__name__)

    @app.route('/')
    def index():
        raise Exception('test')

    rv = app.test_client().get('/', errors_stream=out)
    assert rv.status_code == 500
    assert b'Internal Server Error' in rv.data
    assert not out.getvalue()
