from __future__ import annotations

from http import HTTPStatus

from werkzeug.exceptions import BadRequest
from werkzeug.exceptions import NotFound

from flask import Flask

app = Flask(__name__)


@app.errorhandler(400)
@app.errorhandler(HTTPStatus.BAD_REQUEST)
@app.errorhandler(BadRequest)
def handle_400(e: BadRequest) -> str:
    return ""


@app.errorhandler(ValueError)
def handle_custom(e: ValueError) -> str:
    return ""


@app.errorhandler(ValueError)
def handle_accept_base(e: Exception) -> str:
    return ""


@app.errorhandler(BadRequest)
@app.errorhandler(404)
def handle_multiple(e: BadRequest | NotFound) -> str:
    return ""
