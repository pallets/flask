# -*- coding: utf-8 -*-
"""
    flask
    ~~~~~

    A microframework based on Werkzeug.  It's extensively documented
    and follows best practice patterns.

    :copyright: (c) 2010 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

# utilities we import from Werkzeug and Jinja2 that are unused
# in the module but are exported as public interface.
from werkzeug import abort, redirect
from jinja2 import Markup, escape

from flask.app import Flask
from flask.helpers import url_for, jsonify, json_available, flash, send_file, \
    get_flashed_messages, render_template, render_template, render_template_string, \
    get_template_attribute, json
from flask.globals import current_app, g, request, session, _request_ctx_stack
from flask.module import Module
