# -*- coding: utf-8 -*-
"""
    flask.session
    ~~~~~~~~~~~~~

    This module used to flask with the session global so we moved it
    over to flask.sessions

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from warnings import warn
warn(DeprecationWarning('please use flask.sessions instead'))

from .sessions import SecureCookieSession, NullSession

Session = SecureCookieSession
_NullSession = NullSession
