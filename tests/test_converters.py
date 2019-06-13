from werkzeug.routing import BaseConverter

from flask import has_request_context
from flask import url_for


def test_custom_converters(app, client):
    class ListConverter(BaseConverter):
        def to_python(self, value):
            return value.split(",")

        def to_url(self, value):
            base_to_url = super(ListConverter, self).to_url
            return ",".join(base_to_url(x) for x in value)

    app.url_map.converters["list"] = ListConverter

    @app.route("/<list:args>")
    def index(args):
        return "|".join(args)

    assert client.get("/1,2,3").data == b"1|2|3"

    with app.test_request_context():
        assert url_for("index", args=[4, 5, 6]) == "/4,5,6"


def test_context_available(app, client):
    class ContextConverter(BaseConverter):
        def to_python(self, value):
            assert has_request_context()
            return value

    app.url_map.converters["ctx"] = ContextConverter

    @app.route("/<ctx:name>")
    def index(name):
        return name

    assert client.get("/admin").data == b"admin"
