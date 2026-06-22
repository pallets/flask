from flask import Flask


def test_request_id_header():
    app = Flask(__name__)

    @app.route("/")
    def index():
        return "hello"

    client = app.test_client()
    response = client.get("/")

    assert "X-Request-ID" in response.headers