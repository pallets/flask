import json
from datetime import timedelta

from flask import branch_coverage
from flask import Flask


def save_coverage_to_json(file_path="coverage_result.json"):
    with open(file_path, "w") as json_file:
        json.dump(branch_coverage, json_file, indent=4)


def create_test_app(config):
    app = Flask(__name__)
    app.config.update(config)
    return app


def test_get_send_file_max_age_none():
    app = create_test_app({"SEND_FILE_MAX_AGE_DEFAULT": None})
    with app.app_context():
        max_age = app.get_send_file_max_age("test.txt")
        assert max_age is None
        assert branch_coverage["get_send_file_max_age_1"] == True


def test_get_send_file_max_age_timedelta():
    app = create_test_app({"SEND_FILE_MAX_AGE_DEFAULT": timedelta(hours=1)})
    with app.app_context():
        max_age = app.get_send_file_max_age("test.txt")
        assert max_age == 3600
        assert branch_coverage["get_send_file_max_age_2"] == True


def test_get_send_file_max_age_int():
    app = create_test_app({"SEND_FILE_MAX_AGE_DEFAULT": 3600})
    with app.app_context():
        max_age = app.get_send_file_max_age("test.txt")
        assert max_age == 3600
        assert branch_coverage["get_send_file_max_age_3"] == True


def test_branch_coverage():
    save_coverage_to_json()
    assert branch_coverage["get_send_file_max_age_1"] == True
    assert branch_coverage["get_send_file_max_age_2"] == True
    assert branch_coverage["get_send_file_max_age_3"] == True
