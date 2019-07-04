# -*- coding: utf-8 -*-
"""
    flask
    ~~~~~

    A microframework based on Werkzeug.  It's extensively documented
    and follows best practice patterns.

    :copyright: 2010 Pallets
    :license: BSD-3-Clause
"""
# utilities we import from Werkzeug and Jinja2 that are unused
# in the module but are exported as public interface.
from jinja2 import escape
from jinja2 import Markup
from werkzeug.exceptions import abort
from werkzeug.utils import redirect

from . import json
from .app import Flask
from .app import Request
from .app import Response
from .blueprints import Blueprint
from .config import Config
from .ctx import after_this_request
from .ctx import copy_current_request_context
from .ctx import has_app_context
from .ctx import has_request_context
from .globals import _app_ctx_stack
from .globals import _request_ctx_stack
from .globals import current_app
from .globals import g
from .globals import request
from .globals import session
from .helpers import flash
from .helpers import get_flashed_messages
from .helpers import get_template_attribute
from .helpers import make_response
from .helpers import safe_join
from .helpers import send_file
from .helpers import send_from_directory
from .helpers import stream_with_context
from .helpers import url_for
from .json import jsonify
from .signals import appcontext_popped
from .signals import appcontext_pushed
from .signals import appcontext_tearing_down
from .signals import before_render_template
from .signals import got_request_exception
from .signals import message_flashed
from .signals import request_finished
from .signals import request_started
from .signals import request_tearing_down
from .signals import signals_available
from .signals import template_rendered
from .templating import render_template
from .templating import render_template_string

__version__ = "1.1.0"
