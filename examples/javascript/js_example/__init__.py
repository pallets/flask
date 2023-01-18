from flask import Flask

app = Flask(__name__)

from js_example import views  # noqa: E402, F401
