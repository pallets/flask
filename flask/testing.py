# -*- coding: utf-8 -*-
"""
    flask.testing
    ~~~~~~~~~~~~~

    Implements test support helpers.  This module is lazily imported
    and usually not used in production environments.

    :copyright: (c) 2010 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from werkzeug import Client, EnvironBuilder
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

        as_tuple = kwargs.pop('as_tuple', False)
        buffered = kwargs.pop('buffered', False)
        follow_redirects = kwargs.pop('follow_redirects', False)

        builder = EnvironBuilder(*args, **kwargs)

        if self.application.config.get('SERVER_NAME'):
            server_name = self.application.config.get('SERVER_NAME')
            if ':' not in server_name:
                http_host, http_port = server_name, None
            else:
                http_host, http_port = server_name.split(':', 1)
            if builder.base_url == 'http://localhost/':
                # Default Generated Base URL
                if http_port != None:
                    builder.host = http_host + ':' + http_port
                else:
                    builder.host = http_host
        old = _request_ctx_stack.top
        try:
            return Client.open(self, builder,
                               as_tuple=as_tuple,
                               buffered=buffered,
                               follow_redirects=follow_redirects)
        finally:
            self.context_preserved = _request_ctx_stack.top is not old

    def __enter__(self):
        self.preserve_context = True
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.preserve_context = False
        if self.context_preserved:
            _request_ctx_stack.pop()
