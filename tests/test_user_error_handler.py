# -*- coding: utf-8 -*-
"""
tests.test_user_error_handler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: 2010 Pallets
:license: BSD-3-Clause
"""

from werkzeug.exceptions import (
    Forbidden,
    InternalServerError,
    HTTPException,
    NotFound
    )
import flask


def test_error_handler_no_match(app, client):

    class CustomException(Exception):
        pass

    @app.errorhandler(CustomException)
    def custom_exception_handler(e):
        assert isinstance(e, CustomException)
        return 'custom'

    @app.errorhandler(500)
    def handle_500(e):
        return type(e).__name__

    @app.route('/custom')
    def custom_test():
        raise CustomException()

    @app.route('/keyerror')
    def key_error():
        raise KeyError()

    app.testing = False
    assert client.get('/custom').data == b'custom'
    assert client.get('/keyerror').data == b'KeyError'


def test_error_handler_subclass(app):
    class ParentException(Exception):
        pass

    class ChildExceptionUnregistered(ParentException):
        pass

    class ChildExceptionRegistered(ParentException):
        pass

    @app.errorhandler(ParentException)
    def parent_exception_handler(e):
        assert isinstance(e, ParentException)
        return 'parent'

    @app.errorhandler(ChildExceptionRegistered)
    def child_exception_handler(e):
        assert isinstance(e, ChildExceptionRegistered)
        return 'child-registered'

    @app.route('/parent')
    def parent_test():
        raise ParentException()

    @app.route('/child-unregistered')
    def unregistered_test():
        raise ChildExceptionUnregistered()

    @app.route('/child-registered')
    def registered_test():
        raise ChildExceptionRegistered()

    c = app.test_client()

    assert c.get('/parent').data == b'parent'
    assert c.get('/child-unregistered').data == b'parent'
    assert c.get('/child-registered').data == b'child-registered'


def test_error_handler_http_subclass(app):
    class ForbiddenSubclassRegistered(Forbidden):
        pass

    class ForbiddenSubclassUnregistered(Forbidden):
        pass

    @app.errorhandler(403)
    def code_exception_handler(e):
        assert isinstance(e, Forbidden)
        return 'forbidden'

    @app.errorhandler(ForbiddenSubclassRegistered)
    def subclass_exception_handler(e):
        assert isinstance(e, ForbiddenSubclassRegistered)
        return 'forbidden-registered'

    @app.route('/forbidden')
    def forbidden_test():
        raise Forbidden()

    @app.route('/forbidden-registered')
    def registered_test():
        raise ForbiddenSubclassRegistered()

    @app.route('/forbidden-unregistered')
    def unregistered_test():
        raise ForbiddenSubclassUnregistered()

    c = app.test_client()

    assert c.get('/forbidden').data == b'forbidden'
    assert c.get('/forbidden-unregistered').data == b'forbidden'
    assert c.get('/forbidden-registered').data == b'forbidden-registered'


def test_error_handler_blueprint(app):
    bp = flask.Blueprint('bp', __name__)

    @bp.errorhandler(500)
    def bp_exception_handler(e):
        return 'bp-error'

    @bp.route('/error')
    def bp_test():
        raise InternalServerError()

    @app.errorhandler(500)
    def app_exception_handler(e):
        return 'app-error'

    @app.route('/error')
    def app_test():
        raise InternalServerError()

    app.register_blueprint(bp, url_prefix='/bp')

    c = app.test_client()

    assert c.get('/error').data == b'app-error'
    assert c.get('/bp/error').data == b'bp-error'


def test_default_error_handler():
    bp = flask.Blueprint('bp', __name__)

    @bp.errorhandler(HTTPException)
    def bp_exception_handler(e):
        assert isinstance(e, HTTPException)
        assert isinstance(e, NotFound)
        return 'bp-default'

    @bp.errorhandler(Forbidden)
    def bp_exception_handler(e):
        assert isinstance(e, Forbidden)
        return 'bp-forbidden'

    @bp.route('/undefined')
    def bp_registered_test():
        raise NotFound()

    @bp.route('/forbidden')
    def bp_forbidden_test():
        raise Forbidden()

    app = flask.Flask(__name__)

    @app.errorhandler(HTTPException)
    def catchall_errorhandler(e):
        assert isinstance(e, HTTPException)
        assert isinstance(e, NotFound)
        return 'default'

    @app.errorhandler(Forbidden)
    def catchall_errorhandler(e):
        assert isinstance(e, Forbidden)
        return 'forbidden'

    @app.route('/forbidden')
    def forbidden():
        raise Forbidden()

    @app.route("/slash/")
    def slash():
        return "slash"

    app.register_blueprint(bp, url_prefix='/bp')

    c = app.test_client()
    assert c.get('/bp/undefined').data == b'bp-default'
    assert c.get('/bp/forbidden').data == b'bp-forbidden'
    assert c.get('/undefined').data == b'default'
    assert c.get('/forbidden').data == b'forbidden'
    # Don't handle RequestRedirect raised when adding slash.
    assert c.get("/slash", follow_redirects=True).data == b"slash"
