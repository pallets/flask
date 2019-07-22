#!/usr/bin/env python

from flask import Flask

app = Flask(__name__)

app.route("/")
def hello_world():
    return "Hello, world"


def main():
    app.run(debug=False)

if __name__ == "__main__":
    main()
