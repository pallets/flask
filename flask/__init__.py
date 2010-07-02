# -*- coding: utf-8 -*-
"""
    flask
    ~~~~~

    A microframework based on Werkzeug.  It's extensively documented
    and follows best practice patterns.

    :copyright: (c) 2010 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import with_statement
import os
import sys
import mimetypes
from datetime import datetime, timedelta

# this is a workaround for appengine.  Do not remove this import
import werkzeug

from itertools import chain
from threading import Lock
from jinja2 import Environment, PackageLoader, FileSystemLoader
from werkzeug import Request as RequestBase, Response as ResponseBase, \
     LocalStack, LocalProxy, create_environ, SharedDataMiddleware, \
     ImmutableDict, cached_property, wrap_file, Headers, \
     import_string
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, InternalServerError
from werkzeug.contrib.securecookie import SecureCookie



# utilities we import from Werkzeug and Jinja2 that are unused
# in the module but are exported as public interface.
from werkzeug import abort, redirect
from jinja2 import Markup, escape

# use pkg_resource if that works, otherwise fall back to cwd.  The
# current working directory is generally not reliable with the notable
# exception of google appengine.
try:
    import pkg_resources
    pkg_resources.resource_stream
except (ImportError, AttributeError):
    pkg_resources = None

# a lock used for logger initialization
_logger_lock = Lock()



# context locals
_request_ctx_stack = LocalStack()
current_app = LocalProxy(lambda: _request_ctx_stack.top.app)
request = LocalProxy(lambda: _request_ctx_stack.top.request)
session = LocalProxy(lambda: _request_ctx_stack.top.session)
g = LocalProxy(lambda: _request_ctx_stack.top.g)
