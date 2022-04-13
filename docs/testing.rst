Testing Flask Applications
==========================

Flask provides utilities for testing an application. This documentation
goes over techniques for working with different parts of the application
in tests.

We will use the `pytest`_ framework to set up and run our tests.

.. code-block:: text

    $ pip install pytest

.. _pytest: https://docs.pytest.org/

The :doc:`tutorial </tutorial/index>` goes over how to write tests for
100% coverage of the sample Flaskr blog application. See
:doc:`the tutorial on tests </tutorial/tests>` for a detailed
explanation of specific tests for an application.


Identifying Tests
-----------------

Tests are typically located in the ``tests`` folder. Tests are functions
that start with ``test_``, in Python modules that start with ``test_``.
Tests can also be further grouped in classes that start with ``Test``.

It can be difficult to know what to test. Generally, try to test the
code that you write, not the code of libraries that you use, since they
are already tested. Try to extract complex behaviors as separate
functions to test individually.


Fixtures
--------

Pytest *fixtures* allow writing pieces of code that are reusable across
tests. A simple fixture returns a value, but a fixture can also do
setup, yield a value, then do teardown. Fixtures for the application,
test client, and CLI runner are shown below, they can be placed in
``tests/conftest.py``.

If you're using an
:doc:`application factory </patterns/appfactories>`, define an ``app``
fixture to create and configure an app instance. You can add code before
and after the ``yield`` to set up and tear down other resources, such as
creating and clearing a database.

If you're not using a factory, you already have an app object you can
import and configure directly. You can still use an ``app`` fixture to
set up and tear down resources.

.. code-block:: python

    import pytest
    from my_project import create_app

    @pytest.fixture()
    def app():
        app = create_app()
        app.config.update({
            "TESTING": True,
        })

        # other setup can go here

        yield app

        # clean up / reset resources here


    @pytest.fixture()
    def client(app):
        return app.test_client()


    @pytest.fixture()
    def runner(app):
        return app.test_cli_runner()


Sending Requests with the Test Client
-------------------------------------

The test client makes requests to the application without running a live
server. Flask's client extends
:doc:`Werkzeug's client <werkzeug:test>`, see those docs for additional
information.

The ``client`` has methods that match the common HTTP request methods,
such as ``client.get()`` and ``client.post()``. They take many arguments
for building the request; you can find the full documentation in
:class:`~werkzeug.test.EnvironBuilder`. Typically you'll use ``path``,
``query``, ``headers``, and ``data`` or ``json``.

To make a request, call the method the request should use with the path
to the route to test. A :class:`~werkzeug.test.TestResponse` is returned
to examine the response data. It has all the usual properties of a
response object. You'll usually look at ``response.data``, which is the
bytes returned by the view. If you want to use text, Werkzeug 2.1
provides ``response.text``, or use ``response.get_data(as_text=True)``.

.. code-block:: python

    def test_request_example(client):
        response = client.get("/posts")
        assert b"<h2>Hello, World!</h2>" in response.data


Pass a dict ``query={"key": "value", ...}`` to set arguments in the
query string (after the ``?`` in the URL). Pass a dict ``headers={}``
to set request headers.

To send a request body in a POST or PUT request, pass a value to
``data``. If raw bytes are passed, that exact body is used. Usually,
you'll pass a dict to set form data.


Form Data
~~~~~~~~~

To send form data, pass a dict to ``data``. The ``Content-Type`` header
will be set to ``multipart/form-data`` or
``application/x-www-form-urlencoded`` automatically.

If a value is a file object opened for reading bytes (``"rb"`` mode), it
will be treated as an uploaded file. To change the detected filename and
content type, pass a ``(file, filename, content_type)`` tuple. File
objects will be closed after making the request, so they do not need to
use the usual ``with open() as f:`` pattern.

It can be useful to store files in a ``tests/resources`` folder, then
use ``pathlib.Path`` to get files relative to the current test file.

.. code-block:: python

    from pathlib import Path

    # get the resources folder in the tests folder
    resources = Path(__file__).parent / "resources"

    def test_edit_user(client):
        response = client.post("/user/2/edit", data={
            "name": "Flask",
            "theme": "dark",
            "picture": (resources / "picture.png").open("rb"),
        })
        assert response.status_code == 200


JSON Data
~~~~~~~~~

To send JSON data, pass an object to ``json``. The ``Content-Type``
header will be set to ``application/json`` automatically.

Similarly, if the response contains JSON data, the ``response.json``
attribute will contain the deserialized object.

.. code-block:: python

    def test_json_data(client):
        response = client.post("/graphql", json={
            "query": """
                query User($id: String!) {
                    user(id: $id) {
                        name
                        theme
                        picture_url
                    }
                }
            """,
            variables={"id": 2},
        })
        assert response.json["data"]["user"]["name"] == "Flask"


Following Redirects
-------------------

By default, the client does not make additional requests if the response
is a redirect. By passing ``follow_redirects=True`` to a request method,
the client will continue to make requests until a non-redirect response
is returned.

:attr:`TestResponse.history <werkzeug.test.TestResponse.history>` is
a tuple of the responses that led up to the final response. Each
response has a :attr:`~werkzeug.test.TestResponse.request` attribute
which records the request that produced that response.

.. code-block:: python

    def test_logout_redirect(client):
        response = client.get("/logout")
        # Check that there was one redirect response.
        assert len(response.history) == 1
        # Check that the second request was to the index page.
        assert response.request.path == "/index"


Accessing and Modifying the Session
-----------------------------------

To access Flask's context variables, mainly
:data:`~flask.session`, use the client in a ``with`` statement.
The app and request context will remain active *after* making a request,
until the ``with`` block ends.

.. code-block:: python

    from flask import session

    def test_access_session(client):
        with client:
            client.post("/auth/login", data={"username": "flask"})
            # session is still accessible
            assert session["user_id"] == 1

        # session is no longer accessible

If you want to access or set a value in the session *before* making a
request, use the client's
:meth:`~flask.testing.FlaskClient.session_transaction` method in a
``with`` statement. It returns a session object, and will save the
session once the block ends.

.. code-block:: python

    from flask import session

    def test_modify_session(client):
        with client.session_transaction() as session:
            # set a user id without going through the login route
            session["user_id"] = 1

        # session is saved now

        response = client.get("/users/me")
        assert response.json["username"] == "flask"


.. _testing-cli:

Running Commands with the CLI Runner
------------------------------------

Flask provides :meth:`~flask.Flask.test_cli_runner` to create a
:class:`~flask.testing.FlaskCliRunner`, which runs CLI commands in
isolation and captures the output in a :class:`~click.testing.Result`
object. Flask's runner extends :doc:`Click's runner <click:testing>`,
see those docs for additional information.

Use the runner's :meth:`~flask.testing.FlaskCliRunner.invoke` method to
call commands in the same way they would be called with the ``flask``
command from the command line.

.. code-block:: python

    import click

    @app.cli.command("hello")
    @click.option("--name", default="World")
    def hello_command(name):
        click.echo(f"Hello, {name}!")

    def test_hello_command(runner):
        result = runner.invoke(args="hello")
        assert "World" in result.output

        result = runner.invoke(args=["hello", "--name", "Flask"])
        assert "Flask" in result.output


Tests that depend on an Active Context
--------------------------------------

You may have functions that are called from views or commands, that
expect an active :doc:`application context </appcontext>` or
:doc:`request context  </reqcontext>` because they access ``request``,
``session``, or ``current_app``. Rather than testing them by making a
request or invoking the command, you can create and activate a context
directly.

Use ``with app.app_context()`` to push an application context. For
example, database extensions usually require an active app context to
make queries.

.. code-block:: python

    def test_db_post_model(app):
        with app.app_context():
            post = db.session.query(Post).get(1)

Use ``with app.test_request_context()`` to push a request context. It
takes the same arguments as the test client's request methods.

.. code-block:: python

    def test_validate_user_edit(app):
        with app.test_request_context(
            "/user/2/edit", method="POST", data={"name": ""}
        ):
            # call a function that accesses `request`
            messages = validate_edit_user()

        assert messages["name"][0] == "Name cannot be empty."

Creating a test request context doesn't run any of the Flask dispatching
code, so ``before_request`` functions are not called. If you need to
call these, usually it's better to make a full request instead. However,
it's possible to call them manually.

.. code-block:: python

    def test_auth_token(app):
        with app.test_request_context("/user/2/edit", headers={"X-Auth-Token": "1"}):
            app.preprocess_request()
            assert g.user.name == "Flask"
