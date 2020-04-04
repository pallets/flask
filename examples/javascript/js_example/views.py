from flask import jsonify
from flask import render_template
from flask import request

from js_example import app


@app.route("/", defaults={"js": "plain"})
@app.route("/<any(plain, jquery, fetch):js>")
def index(js):
    return render_template(f"{js}.html", js=js)


@app.route("/add", methods=["POST"])
def add():
    a = request.form.get("a", 0, type=float)
    b = request.form.get("b", 0, type=float)
    return jsonify(result=a + b)
