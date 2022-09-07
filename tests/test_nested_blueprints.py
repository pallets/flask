import pytest

from flask import Blueprint
from flask import Flask

parent = Blueprint("parent", __name__)
child = Blueprint("child", __name__)


def create_app():
    app = Flask(__name__)
    parent.register_blueprint(child, url_prefix="/child")
    app.register_blueprint(parent, url_prefix="/parent")

    return app


@pytest.fixture
def app():
    app = create_app()
    yield app
    parent.reset_blueprint()


def test_1(app):
    pass


def test_2(app):
    pass
