import asyncio

import pytest

from flask import Blueprint
from flask import Flask
from flask import request
from flask.views import MethodView
from flask.views import View

pytest.importorskip("asgiref")


class AppError(Exception):
    pass


class BlueprintError(Exception):
    pass


class AsyncView(View):
    methods = ["GET", "POST"]

    async def dispatch_request(self):
        await asyncio.sleep(0)
        return request.method


class AsyncMethodView(MethodView):
    async def get(self):
        await asyncio.sleep(0)
        return "GET"

    async def post(self):
        await asyncio.sleep(0)
        return "POST"


@pytest.fixture(name="async_app")
def _async_app():
    app = Flask(__name__)

    @app.route("/", methods=["GET", "POST"])
    @app.route("/home", methods=["GET", "POST"])
    async def index():
        await asyncio.sleep(0)
        return request.method

    @app.errorhandler(AppError)
    async def handle(_):
        return "", 412

    @app.route("/error")
    async def error():
        raise AppError()

    blueprint = Blueprint("bp", __name__)

    @blueprint.route("/", methods=["GET", "POST"])
    async def bp_index():
        await asyncio.sleep(0)
        return request.method

    @blueprint.errorhandler(BlueprintError)
    async def bp_handle(_):
        return "", 412

    @blueprint.route("/error")
    async def bp_error():
        raise BlueprintError()

    app.register_blueprint(blueprint, url_prefix="/bp")

    app.add_url_rule("/view", view_func=AsyncView.as_view("view"))
    app.add_url_rule("/methodview", view_func=AsyncMethodView.as_view("methodview"))

    return app


@pytest.mark.parametrize("path", ["/", "/home", "/bp/", "/view", "/methodview"])
def test_async_route(path, async_app):
    test_client = async_app.test_client()
    response = test_client.get(path)
    assert b"GET" in response.get_data()
    response = test_client.post(path)
    assert b"POST" in response.get_data()


@pytest.mark.parametrize("path", ["/error", "/bp/error"])
def test_async_error_handler(path, async_app):
    test_client = async_app.test_client()
    response = test_client.get(path)
    assert response.status_code == 412


def test_async_before_after_request():
    app_first_called = False
    app_before_called = False
    app_after_called = False
    bp_before_called = False
    bp_after_called = False

    app = Flask(__name__)

    @app.route("/")
    def index():
        return ""

    with pytest.deprecated_call():

        @app.before_first_request
        async def before_first():
            nonlocal app_first_called
            app_first_called = True

    @app.before_request
    async def before():
        nonlocal app_before_called
        app_before_called = True

    @app.after_request
    async def after(response):
        nonlocal app_after_called
        app_after_called = True
        return response

    blueprint = Blueprint("bp", __name__)

    @blueprint.route("/")
    def bp_index():
        return ""

    @blueprint.before_request
    async def bp_before():
        nonlocal bp_before_called
        bp_before_called = True

    @blueprint.after_request
    async def bp_after(response):
        nonlocal bp_after_called
        bp_after_called = True
        return response

    app.register_blueprint(blueprint, url_prefix="/bp")

    test_client = app.test_client()
    test_client.get("/")
    assert app_first_called
    assert app_before_called
    assert app_after_called
    test_client.get("/bp/")
    assert bp_before_called
    assert bp_after_called
