The App and Request Context
===========================

The context keeps track of data and objects during a request, CLI command, or
other activity. Rather than passing this data around to every function, the
:data:`.current_app`, :data:`.g`, :data:`.request`, and :data:`.session` proxies
are accessed instead.

When handling a request, the context is referred to as the "request context"
because it contains request data in addition to application data. Otherwise,
such as during a CLI command, it is referred to as the "app context". During an
app context, :data:`.current_app` and :data:`.g` are available, while during a
request context :data:`.request` and :data:`.session` are also available.


Purpose of the Context
----------------------

The context and proxies help solve two development issues: circular imports, and
passing around global data during a request.

The :class:`.Flask` application object has attributes, such as
:attr:`~.Flask.config`, that are useful to access within views and other
functions. However, importing the ``app`` instance within the modules in your
project is prone to circular import issues. When using the
:doc:`app factory pattern </patterns/appfactories>` or writing reusable
:doc:`blueprints </blueprints>` or :doc:`extensions </extensions>` there won't
be an ``app`` instance to import at all.

When the application handles a request, it creates a :class:`.Request` object.
Because a *worker* handles only one request at a time, the request data can be
considered global to that worker during that request. Passing it as an argument
through every function during the request becomes verbose and redundant.

Flask solves these issues with the *active context* pattern. Rather than
importing an ``app`` directly, or having to pass it and the request through to
every single function, you import and access the proxies, which point to the
currently active application and request data. This is sometimes referred to
as "context local" data.


Context During Setup
--------------------

If you try to access :data:`.current_app`, :data:`.g`, or anything that uses it,
outside an app context, you'll get this error message:

.. code-block:: pytb

    RuntimeError: Working outside of application context.

    Attempted to use functionality that expected a current application to be
    set. To solve this, set up an app context using 'with app.app_context()'.
    See the documentation on app context for more information.

If you see that error while configuring your application, such as when
initializing an extension, you can push a context manually since you have direct
access to the ``app``. Use :meth:`.Flask.app_context` in a ``with`` block.

.. code-block:: python

    def create_app():
        app = Flask(__name__)

        with app.app_context():
            init_db()

        return app

If you see that error somewhere else in your code not related to setting up the
application, it most likely indicates that you should move that code into a view
function or CLI command.


Context During Testing
----------------------

See :doc:`/testing` for detailed information about managing the context during
tests.

If you try to access :data:`.request`, :data:`.session`, or anything that uses
it, outside a request context, you'll get this error message:

.. code-block:: pytb

    RuntimeError: Working outside of request context.

    Attempted to use functionality that expected an active HTTP request. See the
    documentation on request context for more information.

This will probably only happen during tests. If you see that error somewhere
else in your code not related to testing, it most likely indicates that you
should move that code into a view function.

The primary way to solve this is to use :meth:`.Flask.test_client` to simulate
a full request.

If you only want to unit test one function, rather than a full request, use
:meth:`.Flask.test_request_context` in a ``with`` block.

.. code-block:: python

    def generate_report(year):
        format = request.args.get("format")
        ...

    with app.test_request_context(
        "/make_report/2017", query_string={"format": "short"}
    ):
        generate_report()


.. _context-visibility:

Visibility of the Context
-------------------------

The context will have the same lifetime as an activity, such as a request, CLI
command, or ``with`` block. Various callbacks and signals registered with the
app will be run during the context.

When a Flask application handles a request, it pushes a requet context
to set the active application and request data. When it handles a CLI command,
it pushes an app context to set the active application. When the activity ends,
it pops that context. Proxy objects like :data:`.request`, :data:`.session`,
:data:`.g`, and :data:`.current_app`, are accessible while the context is pushed
and active, and are not accessible after the context is popped.

The context is unique to each thread (or other worker type). The proxies cannot
be passed to another worker, which has a different context space and will not
know about the active context in the parent's space.

Besides being scoped to each worker, the proxy object has a separate type and
identity than the proxied real object. In some cases you'll need access to the
real object, rather than the proxy. Use the
:meth:`~.LocalProxy._get_current_object` method in those cases.

.. code-block:: python

    app = current_app._get_current_object()
    my_signal.send(app)


Lifecycle of the Context
------------------------

Flask dispatches a request in multiple stages which can affect the request,
response, and how errors are handled. See :doc:`/lifecycle` for a list of all
the steps, callbacks, and signals during each request. The following are the
steps directly related to the context.

-   The app context is pushed, the proxies are available.
-   The :data:`.appcontext_pushed` signal is sent.
-   The request is dispatched.
-   Any :meth:`.Flask.teardown_request` decorated functions are called.
-   The :data:`.request_tearing_down` signal is sent.
-   Any :meth:`.Flask.teardown_appcontext` decorated functions are called.
-   The :data:`.appcontext_tearing_down` signal is sent.
-   The app context is popped, the proxies are no longer available.
-   The :data:`.appcontext_popped` signal is sent.

The teardown callbacks are called by the context when it is popped. They are
called even if there is an unhandled exception during dispatch. They may be
called multiple times in some test scenarios. This means there is no guarantee
that any other parts of the request dispatch have run. Be sure to write these
functions in a way that does not depend on other callbacks and will not fail.


How the Context Works
---------------------

Context locals are implemented using Python's :mod:`contextvars` and Werkzeug's
:class:`~werkzeug.local.LocalProxy`. Python's contextvars are a low level
structure to manage data local to a thread or coroutine. ``LocalProxy`` wraps
the contextvar so that access to any attributes and methods is forwarded to the
object stored in the contextvar.

The context is tracked like a stack, with the active context at the top of the
stack. Flask manages pushing and popping contexts during requests, CLI commands,
testing, ``with`` blocks, etc. The proxies access attributes on the active
context.

Because it is a stack, other contexts may be pushed to change the proxies during
an already active context. This is not a common pattern, but can be used in
advanced use cases. For example, a Flask application can be used as WSGI
middleware, calling another wrapped Flask app from a view.
