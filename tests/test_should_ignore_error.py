import pytest
from flask import Flask

def test_should_ignore_error_deprecation_warning():
    app = Flask(__name__)
    with pytest.warns(DeprecationWarning):
        assert app.should_ignore_error(None) is False