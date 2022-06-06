from __future__ import annotations

from http import HTTPStatus

from flask import Flask
from flask import jsonify
from flask.templating import render_template
from flask.views import View
from flask.wrappers import Response

app = Flask(__name__)


@app.route("/str")
def hello_str() -> str:
    return "<p>Hello, World!</p>"


@app.route("/bytes")
def hello_bytes() -> bytes:
    return b"<p>Hello, World!</p>"


@app.route("/json")
def hello_json() -> Response:
    return jsonify({"response": "Hello, World!"})


@app.route("/status")
@app.route("/status/<int:code>")
def tuple_status(code: int = 200) -> tuple[str, int]:
    return "hello", code


@app.route("/status-enum")
def tuple_status_enum() -> tuple[str, int]:
    return "hello", HTTPStatus.OK


@app.route("/headers")
def tuple_headers() -> tuple[str, dict[str, str]]:
    return "Hello, World!", {"Content-Type": "text/plain"}


@app.route("/template")
@app.route("/template/<name>")
def return_template(name: str | None = None) -> str:
    return render_template("index.html", name=name)


class RenderTemplateView(View):
    def __init__(self: RenderTemplateView, template_name: str) -> None:
        self.template_name = template_name

    def dispatch_request(self: RenderTemplateView) -> str:
        return render_template(self.template_name)


app.add_url_rule(
    "/about",
    view_func=RenderTemplateView.as_view("about_page", template_name="about.html"),
)
