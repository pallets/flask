# -*- coding: utf-8 -*-
"""
    flask.testing
    ~~~~~~~~~~~~~

    Implements test support helpers.  This module is lazily imported
    and usually not used in production environments.

    :copyright: (c) 2010 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from werkzeug import Client
from flask import _request_ctx_stack


class FlaskClient(Client):
    """Works like a regular Werkzeug test client but has some
    knowledge about how Flask works to defer the cleanup of the
    request context stack to the end of a with body when used
    in a with statement.
    """

    preserve_context = context_preserved = False

    def open(self, *args, **kwargs):
        if self.context_preserved:
            _request_ctx_stack.pop()
            self.context_preserved = False
        kwargs.setdefault('environ_overrides', {}) \
            ['flask._preserve_context'] = self.preserve_context
        old = _request_ctx_stack.top
        try:
            return Client.open(self, *args, **kwargs)
        finally:
            self.context_preserved = _request_ctx_stack.top is not old

    def __enter__(self):
        self.preserve_context = True
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.preserve_context = False
        if self.context_preserved:
            _request_ctx_stack.pop()
