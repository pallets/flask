# -*- coding: utf-8 -*-
"""
    flask.session
    ~~~~~~~~~~~~~

    Implements cookie based sessions based on Werkzeug's secure cookie
    system.

    :copyright: (c) 2010 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from werkzeug.contrib.securecookie import SecureCookie


class Session(SecureCookie):
    """Expands the session with support for switching between permanent
    and non-permanent sessions.
    """

    def _get_permanent(self):
        return self.get('_permanent', False)

    def _set_permanent(self, value):
        self['_permanent'] = bool(value)

    permanent = property(_get_permanent, _set_permanent)
    del _get_permanent, _set_permanent


class _NullSession(Session):
    """Class used to generate nicer error messages if sessions are not
    available.  Will still allow read-only access to the empty session
    but fail on setting.
    """

    def _fail(self, *args, **kwargs):
        raise RuntimeError('the session is unavailable because no secret '
                           'key was set.  Set the secret_key on the '
                           'application to something unique and secret.')
    __setitem__ = __delitem__ = clear = pop = popitem = \
        update = setdefault = _fail
    del _fail
