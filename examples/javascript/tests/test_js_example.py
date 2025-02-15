import pytest
from flask import template_rendered


@pytest.mark.parametrize(
    ("path", "template_name"),
    (
        ("/", "fetch.html"),
        ("/plain", "xhr.html"),
        ("/fetch", "fetch.html"),
        ("/jquery", "jquery.html"),
    ),
)
def test_index(app, client, path, template_name):
    """Auto-generated docstring for function test_index."""

    def check(sender, template, context):
        """Auto-generated docstring for function check."""
        assert template.name == template_name

    with template_rendered.connected_to(check, app):
        client.get(path)


@pytest.mark.parametrize(
    ("a", "b", "result"), ((2, 3, 5), (2.5, 3, 5.5), (2, None, 2), (2, "b", 2))
)
def test_add(client, a, b, result):
    """Auto-generated docstring for function test_add."""
    response = client.post("/add", data={"a": a, "b": b})
    assert response.get_json()["result"] == result
