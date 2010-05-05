from time import time
from hashlib import sha1

from openid.association import Association
from openid.store.interface import OpenIDStore
from openid.consumer.consumer import Consumer, SUCCESS, CANCEL
from openid.consumer import discover
from openid.store import nonce

# python-openid is a really stupid library in that regard, we have
# to disable logging by monkey patching
from openid import oidutil
oidutil.log = lambda *a, **kw: None

from flask import request, redirect, abort, url_for, flash, session
from flask_website.database import User, db_session, OpenIDAssociation, \
     OpenIDUserNonce


class WebsiteOpenIDStore(OpenIDStore):
    """Implements the open store for the website using the database."""

    def storeAssociation(self, server_url, association):
        assoc = OpenIDAssociation(
            server_url=server_url,
            handle=association.handle,
            secret=association.secret.encode('base64'),
            issued=association.issued,
            lifetime=association.lifetime,
            assoc_type=association.assoc_type
        )
        db_session.add(assoc)

    def getAssociation(self, server_url, handle=None):
        q = OpenIDAssociation.query.filter_by(server_url=server_url)
        if handle is not None:
            q = q.filter_by(handle=handle)
        result_assoc = None
        for item in q.all():
            assoc = Association(item.handle, item.secret.decode('base64'),
                                item.issued, item.lifetime, item.assoc_type)
            if assoc.getExpiresIn() <= 0:
                self.removeAssociation(server_url, assoc.handle)
            else:
                result_assoc = assoc
        return result_assoc

    def removeAssociation(self, server_url, handle):
        return OpenIDAssociation.query.filter(
            (OpenIDAssociation.server_url == server_url) &
            (OpenIDAssociation.handle == handle)
        ).delete()

    def useNonce(self, server_url, timestamp, salt):
        if abs(timestamp - time()) > nonce.SKEW:
            return False
        rv = OpenIDUserNonce.query.filter(
            (OpenIDUserNonce.server_url == server_url) &
            (OpenIDUserNonce.timestamp == timestamp) &
            (OpenIDUserNonce.salt == salt)
        ).first()
        if rv is not None:
            return False
        rv = OpenIDUserNonce(server_url=server_url, timestamp=timestamp,
                             salt=salt)
        db_session.add(rv)
        return True

    def cleanupNonces(self):
        return OpenIDUserNonce.query.filter(
            OpenIDUserNonce.timestamp <= int(time() - nonce.SKEW)
        ).delete()

    def cleanupAssociations(self):
        return OpenIDAssociation.query.filter(
            OpenIDAssociation.lifetime < int(time())
        ).delete()

    def getAuthKey(self):
        return sha1(config.SECRET_KEY).hexdigest()[:self.AUTH_KEY_LEN]

    def isDump(self):
        return False


def redirect_back():
    return redirect(request.values.get('next') or url_for('general.index'))


def check_return_from_provider():
    if request.args.get('openid_complete') != u'yes':
        return
    try:
        consumer = Consumer(session, WebsiteOpenIDStore())
        openid_response = consumer.complete(request.args.to_dict(),
                                            url_for('general.login',
                                                    _external=True))
        if openid_response.status == SUCCESS:
            return create_or_login(openid_response.identity_url)
        elif openid_response.status == CANCEL:
            flash(u'Error: The request was cancelled')
            return redirect(url_for('general.login'))
        flash(u'Error: OpenID authentication error')
        return redirect(url_for('general.login'))
    finally:
        db_session.commit()


def create_or_login(identity_url):
    session['openid'] = identity_url
    user = User.query.filter_by(openid=identity_url).first()
    if user is None:
        next_url = request.values.get('next')
        return redirect(url_for('general.first_login', next=next_url))
    flash(u'Successfully logged in')
    return redirect_back()


def login(identity_url):
    try:
        try:
            consumer = Consumer(session, WebsiteOpenIDStore())
            auth_request = consumer.begin(identity_url)
        except discover.DiscoveryFailure:
            flash(u'Error: The OpenID was invalid')
            return redirect(url_for('general.login'))
        trust_root = request.host_url
        next_url = request.values.get('next') or url_for('general.index')
        redirect_to = url_for('general.login', openid_complete='yes',
                              next=next_url, _external=True)
        return redirect(auth_request.redirectURL(trust_root, redirect_to))
    finally:
        db_session.commit()
