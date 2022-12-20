# save this as app.py
from flask import flask

app = flask(_name_)

@app.route("/")
def hello():
  return "hello,world!"
