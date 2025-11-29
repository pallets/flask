import pytest
from flask import Flask

def test_should_ignore_error_deprecation_warning():
    """Minimal test: check DeprecationWarning and return value."""
    app = Flask(__name__)
    with pytest.warns(DeprecationWarning):
        assert app.should_ignore_error(None) is False

@pytest.mark.parametrize("error", [Exception(), ValueError(), RuntimeError()])
def test_should_ignore_error_multiple_exceptions(error):
    """Verify that should_ignore_error issues a DeprecationWarning for multiple exception types."""
    app = Flask(__name__)
    with pytest.warns(DeprecationWarning):
        assert app.should_ignore_error(error) is False

def test_should_ignore_error_returns_false():
    """Verify that should_ignore_error always returns False."""
    app = Flask(__name__)
    with pytest.warns(DeprecationWarning):
        result = app.should_ignore_error(Exception())
        assert result is False
