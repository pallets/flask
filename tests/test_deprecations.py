"""Tests for deprecated features."""

import warnings

import pytest

import flask


def test_should_ignore_error_deprecated():
    """Test that should_ignore_error emits a deprecation warning."""
    app = flask.Flask(__name__)

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = app.should_ignore_error(ValueError("test"))

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "should_ignore_error" in str(w[0].message)
        assert "Flask 4.0" in str(w[0].message)
        assert result is False


def test_should_ignore_error_not_called_by_default():
    """Test that should_ignore_error is not called on normal requests."""
    app = flask.Flask(__name__)

    @app.route("/")
    def index():
        return "hello"

    client = app.test_client()

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        response = client.get("/")

        # Should not have any deprecation warnings
        dep_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
        assert len(dep_warnings) == 0
        assert response.status_code == 200


def test_should_ignore_error_override_is_called():
    """Test that overriding should_ignore_error still works for backward compatibility."""

    called = []

    class MyApp(flask.Flask):
        def should_ignore_error(self, error):
            # Track that this was called and call parent to get deprecation warning
            called.append(error)
            super().should_ignore_error(error)
            return False

    app = MyApp(__name__)

    @app.route("/")
    def index():
        raise ValueError("test error")

    client = app.test_client()

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        # Request will return 500 error page
        response = client.get("/")

        # Should have been called with the error
        assert len(called) == 1
        assert isinstance(called[0], ValueError)
        
        # Should have deprecation warning
        dep_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
        assert len(dep_warnings) > 0
        assert any("should_ignore_error" in str(x.message) for x in dep_warnings)
        
        # Should return internal server error
        assert response.status_code == 500
