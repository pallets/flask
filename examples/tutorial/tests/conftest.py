import os
import tempfile

import pytest

from flaskr import create_app
from flaskr.db import get_db
from flaskr.db import init_db

# read in SQL for populating test data
with open(os.path.join(os.path.dirname(__file__), "data.sql"), "rb") as f:
    _data_sql = f.read().decode("utf8")


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    # create the app with common test config
    test_app = create_app({"TESTING": True, "DATABASE": db_path})

    # create the database and load test data
    with test_app.app_context():
        init_db()
        get_db().executescript(_data_sql)

    yield test_app

    # close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app_):
    """A test client for the app."""
    return app_.test_client()


@pytest.fixture
def runner(app_):
    """A test runner for the app's Click commands."""
    return app_.test_cli_runner()


class AuthActions:
    def __init__(self, client_obj):
        self._client = client_obj

    def login(self, username="test", password="test"):
        return self._client.post(
            "/auth/login", data={"username": username, "password": password}
        )

    def logout(self):
        return self._client.get("/auth/logout")


@pytest.fixture
def auth(client):
    return AuthActions(client)
