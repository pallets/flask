Handling Application Errors
===========================

Applications fail, servers fail. Sooner or later you will see an exception
in production. Even if your code is 100% correct, you will still see
exceptions from time to time. Why? Because everything else involved will
fail. Here are some situations where perfectly fine code can lead to server
errors:

-   the client terminated the request early and the application was still
    reading from the incoming data
-   the database server was overloaded and could not handle the query
-   a filesystem is full
-   a harddrive crashed
-   a backend server overloaded
-   a programming error in a library you are using
-   network connection of the server to another system failed

And that's just a small sample of issues you could be facing. So how do we
deal with that sort of problem? By default if your application runs in
production mode, and an exception is raised Flask will display a very simple
page for you and log the exception to the :attr:`~flask.Flask.logger`.

But there is more you can do, and we will cover some better setups to deal
with errors including custom exceptions and 3rd party tools.

Common Error Codes
------------------

The following error codes are some that are often displayed to the user,
even if the application behaves correctly:

*400 Bad Request*
    When the server will not process the request due to something that
    the server perceives to be a client error. Such as malformed request
    syntax, missing query parameters, etc.

*403 Forbidden*
    If you have some kind of access control on your website, you will have
    to send a 403 code for disallowed resources. So make sure the user
    is not lost when they try to access a forbidden resource.

*404 Not Found*
    The good old "chap, you made a mistake typing that URL" message. So
    common that even novices to the internet know that 404 means: damn,
    the thing I was looking for is not there. It's a very good idea to
    make sure there is actually something useful on a 404 page, at least a
    link back to the index.

*410 Gone*
    Did you know that there the "404 Not Found" has a brother named "410
    Gone"? Few people actually implement that, but the idea is that
    resources that previously existed and got deleted answer with 410
    instead of 404. If you are not deleting documents permanently from
    the database but just mark them as deleted, do the user a favour and
    use the 410 code instead and display a message that what they were
    looking for was deleted for all eternity.

*500 Internal Server Error*
    Usually happens on programming errors or if the server is overloaded.
    A terribly good idea is to have a nice page there, because your
    application *will* fail sooner or later.

Error Logging Tools
-------------------

Sending error mails, even if just for critical ones, can become
overwhelming if enough users are hitting the error and log files are
typically never looked at. This is why we recommend using `Sentry
<https://sentry.io/>`_ for dealing with application errors. It's
available as an Open Source project `on GitHub
<https://github.com/getsentry/sentry>`_ and is also available as a `hosted version
<https://sentry.io/signup/>`_ which you can try for free. Sentry
aggregates duplicate errors, captures the full stack trace and local
variables for debugging, and sends you mails based on new errors or
frequency thresholds.

To use Sentry you need to install the `sentry-sdk` client with extra `flask` dependencies::

    $ pip install sentry-sdk[flask]

And then add this to your Flask app::

    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration

    sentry_sdk.init('YOUR_DSN_HERE',integrations=[FlaskIntegration()])

The `YOUR_DSN_HERE` value needs to be replaced with the DSN value you get
from your Sentry installation.

After installation, failures leading to an Internal Server Error
are automatically reported to Sentry and from there you can
receive error notifications.

Follow-up reads:

* Sentry also supports catching errors from your worker queue (RQ, Celery) in a
  similar fashion. See the `Python SDK docs
  <https://docs.sentry.io/platforms/python/>`_ for more information.
* `Getting started with Sentry <https://docs.sentry.io/quickstart/?platform=python>`_
* `Flask-specific documentation <https://docs.sentry.io/platforms/python/flask/>`_.


.. _error-handlers:

Error Handlers
--------------

You might want to show custom error pages to the user when an error occurs.
This can be done by registering error handlers.

An error handler is a function that returns a response when a type of error is
raised, similar to how a view is a function that returns a response when a
request URL is matched. It is passed the instance of the error being handled,
which is most likely a :exc:`~werkzeug.exceptions.HTTPException`.

The status code of the response will not be set to the handler's code. Make
sure to provide the appropriate HTTP status code when returning a response from
a handler.


Registering
```````````

Register handlers by decorating a function with
:meth:`~flask.Flask.errorhandler`. Or use
:meth:`~flask.Flask.register_error_handler` to register the function later.
Remember to set the error code when returning the response.

.. code-block:: python

    @app.errorhandler(werkzeug.exceptions.BadRequest)
    def handle_bad_request(e):
        return 'bad request!', 400

    # or, without the decorator
    app.register_error_handler(400, handle_bad_request)

:exc:`werkzeug.exceptions.HTTPException` subclasses like
:exc:`~werkzeug.exceptions.BadRequest` and their HTTP codes are interchangeable
when registering handlers. (``BadRequest.code == 400``)

Non-standard HTTP codes cannot be registered by code because they are not known
by Werkzeug. Instead, define a subclass of
:class:`~werkzeug.exceptions.HTTPException` with the appropriate code and
register and raise that exception class.

.. code-block:: python

    class InsufficientStorage(werkzeug.exceptions.HTTPException):
        code = 507
        description = 'Not enough storage space.'

    app.register_error_handler(InsufficientStorage, handle_507)

    raise InsufficientStorage()

Handlers can be registered for any exception class, not just
:exc:`~werkzeug.exceptions.HTTPException` subclasses or HTTP status
codes. Handlers can be registered for a specific class, or for all subclasses
of a parent class.


Handling
````````

When building a Flask application you *will* run into exceptions. If some part
of your code breaks while handling a request (and you have no error handlers
registered), a "500 Internal Server Error"
(:exc:`~werkzeug.exceptions.InternalServerError`) will be returned by default.
Similarly, "404 Not Found"
(:exc:`~werkzeug.exceptions.NotFound`) error will occur if a request is sent to an unregistered route.
If a route receives an unallowed request method, a "405 Method Not Allowed"
(:exc:`~werkzeug.exceptions.MethodNotAllowed`) will be raised. These are all
subclasses of :class:`~werkzeug.exceptions.HTTPException` and are provided by
default in Flask.

Flask gives you to the ability to raise any HTTP exception registered by
Werkzeug. However, the default HTTP exceptions return simple exception
pages. You might want to show custom error pages to the user when an error occurs.
This can be done by registering error handlers.

When Flask catches an exception while handling a request, it is first looked up by code.
If no handler is registered for the code, Flask looks up the error by its class hierarchy; the most specific handler is chosen.
If no handler is registered, :class:`~werkzeug.exceptions.HTTPException` subclasses show a
generic message about their code, while other exceptions are converted to a
generic "500 Internal Server Error".

For example, if an instance of :exc:`ConnectionRefusedError` is raised,
and a handler is registered for :exc:`ConnectionError` and
:exc:`ConnectionRefusedError`, the more specific :exc:`ConnectionRefusedError`
handler is called with the exception instance to generate the response.

Handlers registered on the blueprint take precedence over those registered
globally on the application, assuming a blueprint is handling the request that
raises the exception. However, the blueprint cannot handle 404 routing errors
because the 404 occurs at the routing level before the blueprint can be
determined.


Generic Exception Handlers
``````````````````````````

It is possible to register error handlers for very generic base classes
such as ``HTTPException`` or even ``Exception``. However, be aware that
these will catch more than you might expect.

For example, an error handler for ``HTTPException`` might be useful for turning
the default HTML errors pages into JSON. However, this
handler will trigger for things you don't cause directly, such as 404
and 405 errors during routing. Be sure to craft your handler carefully
so you don't lose information about the HTTP error.

.. code-block:: python

    from flask import json
    from werkzeug.exceptions import HTTPException

    @app.errorhandler(HTTPException)
    def handle_exception(e):
        """Return JSON instead of HTML for HTTP errors."""
        # start with the correct headers and status code from the error
        response = e.get_response()
        # replace the body with JSON
        response.data = json.dumps({
            "code": e.code,
            "name": e.name,
            "description": e.description,
        })
        response.content_type = "application/json"
        return response

An error handler for ``Exception`` might seem useful for changing how
all errors, even unhandled ones, are presented to the user. However,
this is similar to doing ``except Exception:`` in Python, it will
capture *all* otherwise unhandled errors, including all HTTP status
codes.

In most cases it will be safer to register handlers for more
specific exceptions. Since ``HTTPException`` instances are valid WSGI
responses, you could also pass them through directly.

.. code-block:: python

    from werkzeug.exceptions import HTTPException

    @app.errorhandler(Exception)
    def handle_exception(e):
        # pass through HTTP errors
        if isinstance(e, HTTPException):
            return e

        # now you're handling non-HTTP exceptions only
        return render_template("500_generic.html", e=e), 500

Error handlers still respect the exception class hierarchy. If you
register handlers for both ``HTTPException`` and ``Exception``, the
``Exception`` handler will not handle ``HTTPException`` subclasses
because it the ``HTTPException`` handler is more specific.


Unhandled Exceptions
````````````````````

When there is no error handler registered for an exception, a 500
Internal Server Error will be returned instead. See
:meth:`flask.Flask.handle_exception` for information about this
behavior.

If there is an error handler registered for ``InternalServerError``,
this will be invoked. As of Flask 1.1.0, this error handler will always
be passed an instance of ``InternalServerError``, not the original
unhandled error.

The original error is available as ``e.original_exception``.
Until Werkzeug 1.0.0, this attribute will only exist during unhandled
errors, use ``getattr`` to get access it for compatibility.

.. code-block:: python

    @app.errorhandler(InternalServerError)
    def handle_500(e):
        original = getattr(e, "original_exception", None)

        if original is None:
            # direct 500 error, such as abort(500)
            return render_template("500.html"), 500

        # wrapped unhandled error
        return render_template("500_unhandled.html", e=original), 500

An error handler for "500 Internal Server Error" will be passed uncaught exceptions in
addition to explicit 500 errors. In debug mode, a handler for "500 Internal Server Error" will not be used.
Instead, the interactive debugger will be shown.


Custom Error Pages
------------------

Sometimes when building a Flask application, you might want to raise a
:exc:`~werkzeug.exceptions.HTTPException` to signal to the user that
something is wrong with the request. Fortunately, Flask comes with a handy
:func:`~flask.abort` function that aborts a request with a HTTP error from
werkzeug as desired. It will also provide a plain black and white error page
for you with a basic description, but nothing fancy.

Depending on the error code it is less or more likely for the user to
actually see such an error.

Consider the code below, we might have a user profile route, and if the user
fails to pass a username we can raise a "400 Bad Request". If the user passes a
username and we can't find it, we raise a "404 Not Found".

.. code-block:: python

    from flask import abort, render_template, request

    # a username needs to be supplied in the query args
    # a successful request would be like /profile?username=jack
    @app.route("/profile")
    def user_profile():
        username = request.arg.get("username")
        # if a username isn't supplied in the request, return a 400 bad request
        if username is None:
            abort(400)

        user = get_user(username=username)
        # if a user can't be found by their username, return 404 not found
        if user is None:
            abort(404)

        return render_template("profile.html", user=user)

Here is another example implementation for a "404 Page Not Found" exception:

.. code-block:: python

    from flask import render_template

    @app.errorhandler(404)
    def page_not_found(e):
        # note that we set the 404 status explicitly
        return render_template('404.html'), 404

When using :doc:`/patterns/appfactories`:

.. code-block:: python

    from flask import Flask, render_template

    def page_not_found(e):
      return render_template('404.html'), 404

    def create_app(config_filename):
        app = Flask(__name__)
        app.register_error_handler(404, page_not_found)
        return app

An example template might be this:

.. code-block:: html+jinja

    {% extends "layout.html" %}
    {% block title %}Page Not Found{% endblock %}
    {% block body %}
      <h1>Page Not Found</h1>
      <p>What you were looking for is just not there.
      <p><a href="{{ url_for('index') }}">go somewhere nice</a>
    {% endblock %}


Further Examples
````````````````

The above examples wouldn't actually be an improvement on the default
exception pages. We can create a custom 500.html template like this:

.. code-block:: html+jinja

    {% extends "layout.html" %}
    {% block title %}Internal Server Error{% endblock %}
    {% block body %}
      <h1>Internal Server Error</h1>
      <p>Oops... we seem to have made a mistake, sorry!</p>
      <p><a href="{{ url_for('index') }}">Go somewhere nice instead</a>
    {% endblock %}

It can be implemented by rendering the template on "500 Internal Server Error":

.. code-block:: python

    from flask import render_template

    @app.errorhandler(500)
    def internal_server_error(e):
        # note that we set the 500 status explicitly
        return render_template('500.html'), 500

When using :doc:`/patterns/appfactories`:

.. code-block:: python

    from flask import Flask, render_template

    def internal_server_error(e):
      return render_template('500.html'), 500

    def create_app():
        app = Flask(__name__)
        app.register_error_handler(500, internal_server_error)
        return app

When using :doc:`/blueprints`:

.. code-block:: python

    from flask import Blueprint

    blog = Blueprint('blog', __name__)

    # as a decorator
    @blog.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    # or with register_error_handler
    blog.register_error_handler(500, internal_server_error)


Blueprint Error Handlers
------------------------

In :doc:`/blueprints`, most error handlers will work as expected.
However, there is a caveat concerning handlers for 404 and 405
exceptions. These error handlers are only invoked from an appropriate
``raise`` statement or a call to ``abort`` in another of the blueprint's
view functions; they are not invoked by, e.g., an invalid URL access.

This is because the blueprint does not "own" a certain URL space, so
the application instance has no way of knowing which blueprint error
handler it should run if given an invalid URL. If you would like to
execute different handling strategies for these errors based on URL
prefixes, they may be defined at the application level using the
``request`` proxy object.

.. code-block:: python

    from flask import jsonify, render_template

    # at the application level
    # not the blueprint level
    @app.errorhandler(404)
    def page_not_found(e):
        # if a request is in our blog URL space
        if request.path.startswith('/blog/'):
            # we return a custom blog 404 page
            return render_template("blog/404.html"), 404
        else:
            # otherwise we return our generic site-wide 404 page
            return render_template("404.html"), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        # if a request has the wrong method to our API
        if request.path.startswith('/api/'):
            # we return a json saying so
            return jsonify(message="Method Not Allowed"), 405
        else:
            # otherwise we return a generic site-wide 405 page
            return render_template("405.html"), 405


Returning API Errors as JSON
----------------------------

When building APIs in Flask, some developers realise that the built-in
exceptions are not expressive enough for APIs and that the content type of
:mimetype:`text/html` they are emitting is not very useful for API consumers.

Using the same techniques as above and :func:`~flask.json.jsonify` we can return JSON
responses to API errors.  :func:`~flask.abort` is called
with a ``description`` parameter. The error handler will
use that as the JSON error message, and set the status code to 404.

.. code-block:: python

    from flask import abort, jsonify

    @app.errorhandler(404)
    def resource_not_found(e):
        return jsonify(error=str(e)), 404

    @app.route("/cheese")
    def get_one_cheese():
        resource = get_resource()

        if resource is None:
            abort(404, description="Resource not found")

        return jsonify(resource)

We can also create custom exception classes. For instance, we can
introduce a new custom exception for an API that can take a proper human readable message,
a status code for the error and some optional payload to give more context
for the error.

This is a simple example:

.. code-block:: python

    from flask import jsonify, request

    class InvalidAPIUsage(Exception):
        status_code = 400

        def __init__(self, message, status_code=None, payload=None):
            super().__init__()
            self.message = message
            if status_code is not None:
                self.status_code = status_code
            self.payload = payload

        def to_dict(self):
            rv = dict(self.payload or ())
            rv['message'] = self.message
            return rv

    @app.errorhandler(InvalidAPIUsage)
    def invalid_api_usage(e):
        return jsonify(e.to_dict())

    # an API app route for getting user information
    # a correct request might be /api/user?user_id=420
    @app.route("/api/user")
    def user_api(user_id):
        user_id = request.arg.get("user_id")
        if not user_id:
            raise InvalidAPIUsage("No user id provided!")

        user = get_user(user_id=user_id)
        if not user:
            raise InvalidAPIUsage("No such user!", status_code=404)

        return jsonify(user.to_dict())

A view can now raise that exception with an error message. Additionally
some extra payload can be provided as a dictionary through the `payload`
parameter.


Logging
-------

See :doc:`/logging` for information on how to log exceptions, such as by
emailing them to admins.

Debugging Application Errors
============================

For production applications, configure your application with logging and
notifications as described in :doc:`/logging`. This section provides
pointers when debugging deployment configuration and digging deeper with a
full-featured Python debugger.

When in Doubt, Run Manually
---------------------------

Having problems getting your application configured for production? If you
have shell access to your host, verify that you can run your application
manually from the shell in the deployment environment. Be sure to run under
the same user account as the configured deployment to troubleshoot permission
issues. You can use Flask's builtin development server with `debug=True` on
your production host, which is helpful in catching configuration issues, but
**be sure to do this temporarily in a controlled environment.** Do not run in
production with `debug=True`.


.. _working-with-debuggers:

Working with Debuggers
----------------------

The built-in development server provides a :ref:`debug-mode` that shows
an interactive traceback in the browser when an unhandled error occurs
during a request.

External debuggers, such as those provided by IDEs, can offer a much
more powerful and visual debugging experience. They can also be used to
step through code during a request before an error is raised, or if no
error is raised.

When using an external debugger, the app should still be in debug mode,
but it can be useful to disable the built-in debugger and reloader,
which can interfere.

When running from the command line:

.. code-block:: text

    $ export FLASK_ENV=development
    $ flask run --no-debugger --no-reload

When running from Python:

.. code-block:: python

    app.run(debug=True, use_debugger=False, use_reloader=False)

Disabling these isn't required, an external debugger will continue to
work with the following caveats. If the built-in debugger is not
disabled, it will catch unhandled exceptions before the external
debugger can. If the reloader is not disabled, it could cause an
unexpected reload if code changes during debugging.
