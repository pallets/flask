import pytest
from flask import Flask, jsonify

def test_jsonify_mimetype_and_content_type_invariance():
    """Verify jsonify sets application/json mimetype and content-type header."""
    app = Flask(__name__)
    
    @app.route("/api/ping")
    def ping():
        return jsonify(status="ok", code=200)

    with app.test_client() as client:
        response = client.get("/api/ping")
        assert response.status_code == 200
        assert response.mimetype == "application/json"
        assert "application/json" in response.headers.get("Content-Type", "")
        assert response.json == {"status": "ok", "code": 200}

def test_jsonify_empty_dictionary():
    app = Flask(__name__)
    
    @app.route("/api/empty")
    def empty():
        return jsonify({})

    with app.test_client() as client:
        response = client.get("/api/empty")
        assert response.status_code == 200
        assert response.json == {}
