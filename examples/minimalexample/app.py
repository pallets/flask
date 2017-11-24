from flask import Flask

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    return "Hello world!"

app.run(debug=True)
