from yourapplication import app
import pytest

@pytest.fixture
def client():
    app.config['TESTING'] = True
    client = app.test_client()
    return client

def test_index(client):
    rv = client.get('/')
    assert b"Hello World!" in rv.data