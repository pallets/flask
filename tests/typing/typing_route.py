from __future__ import annotations

import typing as t
from http import HTTPStatus

from flask import Flask
from flask import jsonify
from flask import stream_template
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


@app.route("/generator")
def hello_generator() -> t.Generator[str, None, None]:
    def show() -> t.Generator[str, None, None]:
        for x in range(100):
            yield f"data:{x}\n\n"

    return show()


@app.route("/generator-expression")
def hello_generator_expression() -> t.Iterator[bytes]:
    return (f"data:{x}\n\n".encode() for x in range(100))


@app.route("/iterator")
def hello_iterator() -> t.Iterator[str]:
    return iter([f"data:{x}\n\n" for x in range(100)])


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


@app.route("/template")
def return_template_stream() -> t.Iterator[str]:
    return stream_template("index.html", name="Hello")


class RenderTemplateView(View):
    def __init__(self: RenderTemplateView, template_name: str) -> None:
        self.template_name = template_name

    def dispatch_request(self: RenderTemplateView) -> str:
        return render_template(self.template_name)


app.add_url_rule(
    "/about",
    view_func=RenderTemplateView.as_view("about_page", template_name="about.html"),
)
