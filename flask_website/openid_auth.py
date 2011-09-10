from time import time

from openid.association import Association
from openid.store.interface import OpenIDStore
from openid.store import nonce

from flask_website.database import db_session, OpenIDAssociation, \
     OpenIDUserNonce


class DatabaseOpenIDStore(OpenIDStore):
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
        db_session.commit()

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
        try:
            return OpenIDAssociation.query.filter(
                (OpenIDAssociation.server_url == server_url) &
                (OpenIDAssociation.handle == handle)
            ).delete()
        finally:
            db_session.commit()

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
        db_session.commit()
        return True

    def cleanupNonces(self):
        try:
            return OpenIDUserNonce.query.filter(
                OpenIDUserNonce.timestamp <= int(time() - nonce.SKEW)
            ).delete()
        finally:
            db_session.commit()

    def cleanupAssociations(self):
        try:
            return OpenIDAssociation.query.filter(
                OpenIDAssociation.lifetime < int(time())
            ).delete()
        finally:
            db_session.commit()
