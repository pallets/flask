# -*- coding: utf-8 -*-
from werkzeug.exceptions import Forbidden, InternalServerError
import flask


def test_error_handler_no_match():
    app = flask.Flask(__name__)

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

    c = app.test_client()

    assert c.get('/custom').data == b'custom'
    assert c.get('/keyerror').data == b'KeyError'


def test_error_handler_subclass():
    app = flask.Flask(__name__)

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


def test_error_handler_http_subclass():
    app = flask.Flask(__name__)

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


def test_error_handler_blueprint():
    bp = flask.Blueprint('bp', __name__)

    @bp.errorhandler(500)
    def bp_exception_handler(e):
        return 'bp-error'

    @bp.route('/error')
    def bp_test():
        raise InternalServerError()

    app = flask.Flask(__name__)

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
