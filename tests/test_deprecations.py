import pytest

from flask import json_available


def test_json_available():
    with pytest.deprecated_call() as rec:
        assert json_available
        assert json_available == True  # noqa E712
        assert json_available != False  # noqa E712

    assert len(rec.list) == 3
