from flask import Flask

app = Flask(__name__)

# Returns "Hello World!" when "/" is accessed by the user
@app.route("/")
def hello():
    return "Hello World!"
