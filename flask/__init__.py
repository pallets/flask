# -*- coding: utf-8 -*-
"""
    flask
    ~~~~~

    A microframework based on Werkzeug.  It's extensively documented
    and follows best practice patterns.

    :copyright: © 2010 by the Pallets team.
    :license: BSD, see LICENSE for more details.
"""

__version__ = '1.1.dev'

# utilities we import from Werkzeug and Jinja2 that are unused
# in the module but are exported as public interface.
from werkzeug.exceptions import abort
from werkzeug.utils import redirect
from jinja2 import Markup, escape

from .app import Flask, Request, Response
from .config import Config
from .helpers import (url_for, flash, send_file, send_from_directory,
     get_flashed_messages, get_template_attribute, make_response, safe_join,
     stream_with_context)
from .globals import (current_app, g, request, session, _request_ctx_stack,
     _app_ctx_stack)
from .ctx import (has_request_context, has_app_context,
     after_this_request, copy_current_request_context)
from .blueprints import Blueprint
from .templating import render_template, render_template_string
from .signals import (signals_available, template_rendered, request_started,
     request_finished, got_request_exception, request_tearing_down,
     appcontext_tearing_down, appcontext_pushed,
     appcontext_popped, message_flashed, before_render_template)

# Expose a convenient wrapper around python's builtin json module.
from .json import jsonify

# backwards compat, goes away in 1.0
from .sessions import SecureCookieSession as Session
json_available = True
