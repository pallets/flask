import pytest
from flask import Flask, render_template_string

def test_template_filter_without_parentheses():
    app = Flask(__name__)

    @app.template_filter
    def double(x):
        return x * 2

    with app.app_context():
        output = render_template_string("{{ 2 | double }}")
        assert output == "4"

def test_template_filter_with_parentheses():
    app = Flask(__name__)

    @app.template_filter()
    def triple(x):
        return x * 3

    with app.app_context():
        output = render_template_string("{{ 3 | triple }}")
        assert output == "9"
