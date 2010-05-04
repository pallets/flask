# -*- coding: utf-8 -*-
"""
    simpleopenid
    ~~~~~~~~~~~~

    Tiny wrapper around python-openid to make working with the basic
    API in a flask application easier.  Adapt this code for your own
    project if necessary.

    :copyright: (c) 2010 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from functools import wraps

from flask import request, session, flash, redirect
from werkzeug import url_quote

from openid.association import Association
from openid.store.interface import OpenIDStore
from openid.store.filestore import FileOpenIDStore
from openid.consumer.consumer import Consumer, SUCCESS, CANCEL
from openid.consumer import discover
from openid.store import nonce

# python-openid is a really stupid library in that regard, we have
# to disable logging by monkey patching
from openid import oidutil
oidutil.log = lambda *a, **kw: None


class SimpleOpenID(object):
    """Simple helper class for OpenID auth."""

    def __init__(self, store_path):
        self.store_path = store_path
        self.after_login_func = None

    def create_store(self):
        """Creates the filesystem store"""
        return FileOpenIDStore(self.store_path)

    def signal_error(self, msg):
        """Signals an error.  It does this by flashing a message"""
        flash(u'Error: ' + msg)

    def get_next_url(self):
        """Return the URL where we want to redirect to."""
        return request.values.get('next') or \
               request.referrer or \
               request.url_root

    def get_current_url(self):
        """the current URL + next"""
        return request.base_url + '?next=' + url_quote(self.get_next_url())

    def get_success_url(self):
        """Return the success URL"""
        return self.get_current_url() + '&openid_complete=yes'

    def errorhandler(f):
        """Called if an error occours with the message.  By default
        ``'Error: message'`` is flashed.
        """
        self.signal_error = f
        return f

    def after_login(self, f):
        """This function will be called after login.  It must redirect to
        a different place and remember the user somewhere.  The session
        is not modified by SimpleOpenID.
        """
        self.after_login_func = f
        return f

    def loginhandler(self, f):
        """Marks a function as login handler.  This decorator injects some
        more OpenID required logic.
        """
        self.login_endpoint = f.__name__
        @wraps(f)
        def decorated(*args, **kwargs):
            if request.args.get('openid_complete') != u'yes':
                return f(*args, **kwargs)
            consumer = Consumer(session, self.create_store())
            openid_response = consumer.complete(request.args.to_dict(),
                                                self.get_current_url())
            if openid_response.status == SUCCESS:
                return self.after_login_func(openid_response.identity_url)
            elif openid_response.status == CANCEL:
                self.signal_error(u'The request was cancelled')
                return redirect(self.get_current_url())
            self.signal_error(u'OpenID authentication error')
            return redirect(self.get_current_url())
        return decorated

    def try_login(self, identity_url):
        """This tries to login with the given identity URL.  This function
        must be called from the login_handler.
        """
        try:
            consumer = Consumer(session, self.create_store())
            auth_request = consumer.begin(identity_url)
        except discover.DiscoveryFailure:
            self.signal_error(u'The OpenID was invalid')
            return redirect(self.get_current_url())
        trust_root = request.host_url
        return redirect(auth_request.redirectURL(request.host_url,
                                                 self.get_success_url()))
