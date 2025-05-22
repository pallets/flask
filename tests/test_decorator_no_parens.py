import pytest

import flask


def test_template_filter_no_parens(app):
    """Test that @app.template_filter works without parentheses."""
    @app.template_filter
    def double(x):
        return x * 2

    assert "double" in app.jinja_env.filters
    assert app.jinja_env.filters["double"] == double
    assert app.jinja_env.filters["double"](2) == 4


def test_template_test_no_parens(app):
    """Test that @app.template_test works without parentheses."""
    @app.template_test
    def is_even(x):
        return x % 2 == 0

    assert "is_even" in app.jinja_env.tests
    assert app.jinja_env.tests["is_even"] == is_even
    assert app.jinja_env.tests["is_even"](2) is True
    assert app.jinja_env.tests["is_even"](3) is False


def test_template_global_no_parens(app):
    """Test that @app.template_global works without parentheses."""
    @app.template_global
    def get_answer():
        return 42

    assert "get_answer" in app.jinja_env.globals
    assert app.jinja_env.globals["get_answer"] == get_answer
    assert app.jinja_env.globals["get_answer"]() == 42


def test_blueprint_app_template_filter_no_parens(app):
    """Test that @blueprint.app_template_filter works without parentheses."""
    bp = flask.Blueprint("test_bp", __name__)

    @bp.app_template_filter
    def triple(x):
        return x * 3

    app.register_blueprint(bp)
    assert "triple" in app.jinja_env.filters
    assert app.jinja_env.filters["triple"](3) == 9


def test_blueprint_app_template_test_no_parens(app):
    """Test that @blueprint.app_template_test works without parentheses."""
    bp = flask.Blueprint("test_bp", __name__)

    @bp.app_template_test
    def is_odd(x):
        return x % 2 == 1

    app.register_blueprint(bp)
    assert "is_odd" in app.jinja_env.tests
    assert app.jinja_env.tests["is_odd"](3) is True
    assert app.jinja_env.tests["is_odd"](2) is False


def test_blueprint_app_template_global_no_parens(app):
    """Test that @blueprint.app_template_global works without parentheses."""
    bp = flask.Blueprint("test_bp", __name__)

    @bp.app_template_global
    def get_pi():
        return 3.14

    app.register_blueprint(bp)
    assert "get_pi" in app.jinja_env.globals
    assert app.jinja_env.globals["get_pi"]() == 3.14
