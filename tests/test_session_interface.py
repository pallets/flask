import flask
from flask.sessions import SessionInterface


def test_open_session_endpoint_not_none():
    # Define a session interface that breaks if request.endpoint is None
    class MySessionInterface(SessionInterface):
        def save_session(self):
            pass

        def open_session(self, _, request):
            assert request.endpoint is not None

    def index():
        return "Hello World!"

    # Confirm a 200 response, indicating that request.endpoint was NOT None
    app = flask.Flask(__name__)
    app.route("/")(index)
    app.session_interface = MySessionInterface()
    response = app.test_client().open("/")
    assert response.status_code == 200
