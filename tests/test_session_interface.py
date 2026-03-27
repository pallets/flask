import pytest

import flask
from flask.globals import app_ctx
from flask.sessions import SessionInterface


def test_open_session_with_endpoint():
    """If request.endpoint (or other URL matching behavior) is needed
    while loading the session, RequestContext.match_request() can be
    called manually.
    """

    class MySessionInterface(SessionInterface):
        def save_session(self, app, session, response):
            pass

        def open_session(self, app, request):
            app_ctx.match_request()
            assert request.endpoint is not None

    app = flask.Flask(__name__)
    app.session_interface = MySessionInterface()

    @app.get("/")
    def index():
        return "Hello, World!"

    response = app.test_client().get("/")
    assert response.status_code == 200


def test_save_session_without_secret_key(app):
    app.secret_key = "test key"
    session = app.session_interface.session_class({"foo": "bar"})
    session.modified = True
    app.secret_key = None

    with pytest.raises(RuntimeError) as e:
        app.session_interface.save_session(app, session, app.response_class())

    assert e.value.args and "session is unavailable" in e.value.args[0]
    assert "no secret key was set" in e.value.args[0]
