import flask


def test_rate_limit_disabled_by_default():
    app = flask.Flask(__name__)

    @app.route("/")
    def index():
        return "ok"

    client = app.test_client()

    for _ in range(3):
        rv = client.get("/")
        assert rv.status_code == 200


def test_rate_limit_blocks_after_threshold():
    app = flask.Flask(__name__)
    app.config.update(
        RATELIMIT_ENABLED=True,
        RATELIMIT_REQUESTS=2,
        RATELIMIT_WINDOW=60,
    )

    @app.route("/")
    def index():
        return "ok"

    client = app.test_client()

    assert client.get("/").status_code == 200
    assert client.get("/").status_code == 200

    rv = client.get("/")
    assert rv.status_code == 429
