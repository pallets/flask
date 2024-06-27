import pytest
from werkzeug.exceptions import InternalServerError
from werkzeug.exceptions import NotFound

from flask import branch_coverage
from flask import Flask
from flask import json
from flask import track_coverage


def create_app():
    app = Flask(__name__)

    @app.route("/success")
    def success():
        track_coverage("dispatch_request_success")
        return "Success", 200

    @app.route("/error")
    def error():
        track_coverage("dispatch_request_error")
        raise InternalServerError(description="Error occurred")

    @app.route("/not_found")
    def not_found():
        track_coverage("dispatch_request_not_found")
        raise NotFound(description="This is a 404")

    return app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_success_path(client):
    response = client.get("/success")
    assert response.status_code == 200
    assert response.data == b"Success"
    assert branch_coverage["dispatch_request_success"]


def test_error_handling(client):
    response = client.get("/error")
    assert response.status_code == 500
    assert "Error occurred" in response.get_data(as_text=True)
    assert branch_coverage["dispatch_request_error"]


def test_not_found_handling(client):
    response = client.get("/not_found")
    assert response.status_code == 404
    assert "This is a 404" in response.get_data(as_text=True)
    assert branch_coverage["dispatch_request_not_found"]


def test_no_route(client):
    response = client.get("/no_route")
    assert response.status_code == 404


def save_coverage_to_json(file_path="coverage_result.json"):
    with open(file_path, "w") as json_file:
        json.dump(branch_coverage, json_file, indent=4)
