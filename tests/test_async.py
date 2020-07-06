import asyncio

import pytest

from flask import abort
from flask import Flask
from flask import request


@pytest.fixture(name="async_app")
def _async_app():
    app = Flask(__name__)

    @app.route("/", methods=["GET", "POST"])
    async def index():
        await asyncio.sleep(0)
        return request.method

    @app.route("/error")
    async def error():
        abort(412)

    return app


def test_async_request_context(async_app):
    test_client = async_app.test_client()
    response = test_client.get("/")
    assert b"GET" in response.get_data()
    response = test_client.post("/")
    assert b"POST" in response.get_data()
    response = test_client.get("/error")
    assert response.status_code == 412
