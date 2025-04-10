Single-Page Applications
========================

Flask can be used to serve Single-Page Applications (SPA) by placing static
files produced by your frontend framework in a subfolder inside of your
project. You will also need to create a catch-all endpoint that routes all
requests to your SPA.

The following example demonstrates how to serve an SPA along with an API::

    from flask import Flask, jsonify

    app = Flask(__name__, static_folder='app', static_url_path="/app")


    @app.route("/heartbeat")
    def heartbeat():
        return jsonify({"status": "healthy"})


    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def catch_all(path):
        return app.send_static_file("index.html")
