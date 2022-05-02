from http import HTTPStatus
from typing import Tuple
from typing import Union

from flask import Flask
from flask import jsonify
from flask.templating import render_template
from flask.views import View
from flask.wrappers import Response


app = Flask(__name__)


@app.route("/")
def hello_world() -> str:
    return "<p>Hello, World!</p>"


@app.route("/json")
def hello_world_json() -> Response:
    return jsonify({"response": "Hello, World!"})


@app.route("/template")
@app.route("/template/<name>")
def return_template(name: Union[str, None] = None) -> str:
    return render_template("index.html", name=name)


@app.errorhandler(HTTPStatus.INTERNAL_SERVER_ERROR)
def error_500(e) -> Tuple[str, int]:
    return "<p>Sorry, we are having problems</p>", HTTPStatus.INTERNAL_SERVER_ERROR


@app.before_request
def before_request() -> None:
    app.logger.debug("Executing a sample before_request function")
    return None


class RenderTemplateView(View):
    def __init__(self: "RenderTemplateView", template_name: str) -> None:
        self.template_name = template_name

    def dispatch_request(self: "RenderTemplateView") -> str:
        return render_template(self.template_name)


app.add_url_rule(
    "/about",
    view_func=RenderTemplateView.as_view("about_page", template_name="about.html"),
)
