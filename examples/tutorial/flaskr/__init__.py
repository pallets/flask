import os

from flask import Flask
#   Import limiter for brute-force protection
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address



def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
 
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY="dev",
        # store the database in the instance folder
        DATABASE=os.path.join(app.instance_path, "flaskr.sqlite"),
    )
    #   Secure session cookie settings for production safety
    app.config.update(
        SESSION_COOKIE_SECURE=True,      # Cookie sent only over HTTPS
        SESSION_COOKIE_HTTPONLY=True,    # Prevent JavaScript access (XSS protection)
        SESSION_COOKIE_SAMESITE="Lax",   # Helps protect against CSRF
    )
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    # ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)
    # Initialize rate limiter to prevent brute-force login attacks
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],  # Global safety limits
    )
    # Make limiter accessible inside other files (like auth.py)
    app.extensions["limiter"] = limiter

    @app.route("/hello")
    def hello():
        return "Hello, World!"

    # register the database commands
    from . import db

    db.init_app(app)

    # apply the blueprints to the app
    from . import auth
    from . import blog

    app.register_blueprint(auth.bp)
    app.register_blueprint(blog.bp)

    # make url_for('index') == url_for('blog.index')
    # in another app, you might define a separate main index here with
    # app.route, while giving the blog blueprint a url_prefix, but for
    # the tutorial the blog will be the main index
    app.add_url_rule("/", endpoint="index")

    return app