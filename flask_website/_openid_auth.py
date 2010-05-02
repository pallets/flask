from __future__ import with_statement

from time import time
from hashlib import sha1
from contextlib import closing

from openid.association import Association
from openid.store.interface import OpenIDStore
from openid.consumer.consumer import Consumer, SUCCESS, CANCEL
from openid.consumer import discover
from openid.store import nonce

from sqlalchemy.orm import scoped_session
from sqlalchemy.exceptions import SQLError

from flask import request, redirect, abort, url_for, flash
from flask_website.database import User, db_session


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
        return OpenIDAssociation.filter(
            (OpenIDAssociation.server_url == server_url) &
            (OpenIDAssociation.handle == handle)
        ).delete()

    def useNonce(self, server_url, timestamp, salt):
        if abs(timestamp - time()) > nonce.SKEW:
            return False
        rv = OpenIDUserNonces.query.filter(
            (OpenIDUserNonces.server_url == server_url) &
            (OpenIDUserNonces.timestamp == timestamp) &
            (OpenIDUserNonces.salt == salt)
        ).first()
        if rv is not None:
            return False
        rv = OpenIDUserNonces(server_url=server_url, timestamp=timestamp,
                              salt=salt)
        session.add(rv)
        return True

    def cleanupNonces(self):
        return OpenIDUserNonces.filter(
            OpenIDUserNonces.timestamp <= int(time() - nonce.SKEW)
        ).delete()

    def cleanupAssociations(self):
        return OpenIDAssociation.filter(
            OpenIDAssociation.lifetime < int(time())
        ).delete()

    def getAuthKey(self):
        return sha1(config.SECRET_KEY).hexdigest()[:self.AUTH_KEY_LEN]

    def isDump(self):
        return False
