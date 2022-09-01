from flask import Flask
from flask_wtf.csrf import CSRFProtect

# OpenRefactory Warning: The 'Flask' method creates a Flask app
# without Cross-Site Request Forgery (CSRF) protection.
app = Flask(__name__)
CSRFProtect(app)

from js_example import views  # noqa: F401
