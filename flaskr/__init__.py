import os

from flask import Flask, request, g
import markdown


def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    # app = Flask(__name__, instance_relative_config=True)
    app = Flask(__name__, instance_path='/tmp')
    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY="dev",
        # store the database in the instance folder
        DATABASE=os.path.join(app.instance_path, "flaskr.sqlite"),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route("/hello")
    def hello():
        return "Hello, World!"

    @app.before_request
    def load_theme_preference():
        theme = request.cookies.get('theme')
        if theme:
            g.theme = theme
        else:
            g.theme = 'dark' if request.user_agent.platform in ['android', 'iphone'] and request.user_agent.browser in ['chrome', 'safari'] and request.user_agent.string.find('DarkMode') != -1 else 'light'

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
