from markupsafe import escape
from markupsafe import Markup

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
from .globals import current_app
from .globals import g
from .globals import request
from .globals import session
from .helpers import abort
from .helpers import flash
from .helpers import get_flashed_messages
from .helpers import get_template_attribute
from .helpers import make_response
from .helpers import redirect
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
from .templating import stream_template
from .templating import stream_template_string

__version__ = "2.3.0.dev"


def __getattr__(name):
    if name == "_app_ctx_stack":
        import warnings

        from .globals import __app_ctx_stack

        warnings.warn(
            "'_app_ctx_stack' is deprecated and will be removed in Flask 2.3.",
            DeprecationWarning,
            stacklevel=2,
        )
        return __app_ctx_stack

    if name == "_request_ctx_stack":
        import warnings

        from .globals import __request_ctx_stack

        warnings.warn(
            "'_request_ctx_stack' is deprecated and will be removed in Flask 2.3.",
            DeprecationWarning,
            stacklevel=2,
        )
        return __request_ctx_stack

    raise AttributeError(name)
