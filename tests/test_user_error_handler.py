# -*- coding: utf-8 -*-
import itertools
import flask


def test_register_error_handler_the_right_order():
    class BasicException(Exception):
        pass

    class E1(BasicException):
        pass

    class E2(E1):
        pass

    class E3(E2):
        pass

    class E4(E3):
        pass

    app = flask.Flask(__name__)

    def f(e):
        return 'boom'

    for e1, e2, e3, e4, e in itertools.permutations(
            (E1, E2, E3, E4, BasicException)):
        app.register_error_handler(e1, f)
        app.register_error_handler(e2, f)
        app.register_error_handler(e3, f)
        app.register_error_handler(e4, f)
        app.register_error_handler(e, f)
        error_handlers = app.error_handler_spec[None][None]
        assert error_handlers[0] == (E4, f)
        assert error_handlers[1] == (E3, f)
        assert error_handlers[2] == (E2, f)
        assert error_handlers[3] == (E1, f)
        assert error_handlers[4] == (BasicException, f)
        app.error_handler_spec[None][None] = []


def test_error_handler_call_order():
    app = flask.Flask(__name__)

    class ParentException(Exception):
        pass

    class ChildException(ParentException):
        pass

    @app.errorhandler(ParentException)
    def my_decorator_exception_handler(e):
        assert isinstance(e, ParentException)
        return 'parent'

    @app.errorhandler(ChildException)
    def my_function_exception_handler(e):
        assert isinstance(e, ChildException)
        return 'child'

    @app.route('/parent')
    def blue_deco_test():
        raise ParentException()

    @app.route('/child')
    def blue_func_test():
        raise ChildException()


    c = app.test_client()

    assert c.get('/parent').data == b'parent'
    assert c.get('/child').data == b'child'
