from flask import Blueprint
from flask import render_template

frontend = Blueprint("frontend", __name__, template_folder="templates")


@frontend.route("/")
def index():
    return render_template("frontend/index.html")


@frontend.route("/missing")
def missing_template():
    return render_template("missing_template.html")
