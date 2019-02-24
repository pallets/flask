from flask.globals import _app_ctx_stack


def test_custom_converters(app, client):
    from werkzeug.routing import BaseConverter

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


def test_model_converters(app, client):
    from werkzeug.routing import BaseConverter

    class ModelConverterTester(BaseConverter):
        def to_python(self, value):
            assert _app_ctx_stack.top is not None
            return value

    app.url_map.converters["model"] = ModelConverterTester

    @app.route("/<model:user_name>")
    def index(user_name):
        return user_name, 200

    client.get("/admin").data
