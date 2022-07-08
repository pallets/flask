.. _async_await:

Using ``async`` and ``await``
=============================

.. versionadded:: 2.0

Routes, error handlers, before request, after request, and teardown
functions can all be coroutine functions if Flask is installed with the
``async`` extra (``pip install flask[async]``). This allows views to be
defined with ``async def`` and use ``await``.

.. code-block:: python

    @app.route("/get-data")
    async def get_data():
        data = await async_db_query(...)
        return jsonify(data)

Pluggable class-based views also support handlers that are implemented as
coroutines. This applies to the :meth:`~flask.views.View.dispatch_request`
method in views that inherit from the :class:`flask.views.View` class, as
well as all the HTTP method handlers in views that inherit from the
:class:`flask.views.MethodView` class.

.. admonition:: Using ``async`` on Windows on Python 3.8

    Python 3.8 has a bug related to asyncio on Windows. If you encounter
    something like ``ValueError: set_wakeup_fd only works in main thread``,
    please upgrade to Python 3.9.

.. admonition:: Using ``async`` with greenlet

    When using gevent or eventlet to serve an application or patch the
    runtime, greenlet>=1.0 is required. When using PyPy, PyPy>=7.3.7 is
    required.


Performance
-----------

Async functions require an event loop to run. Flask, as a WSGI
application, uses one worker to handle one request/response cycle.
When a request comes in to an async view, Flask will start an event loop
in a thread, run the view function there, then return the result.

Each request still ties up one worker, even for async views. The upside
is that you can run async code within a view, for example to make
multiple concurrent database queries, HTTP requests to an external API,
etc. However, the number of requests your application can handle at one
time will remain the same.

**Async is not inherently faster than sync code.** Async is beneficial
when performing concurrent IO-bound tasks, but will probably not improve
CPU-bound tasks. Traditional Flask views will still be appropriate for
most use cases, but Flask's async support enables writing and using
code that wasn't possible natively before.


Background tasks
----------------

Async functions will run in an event loop until they complete, at
which stage the event loop will stop. This means any additional
spawned tasks that haven't completed when the async function completes
will be cancelled. Therefore you cannot spawn background tasks, for
example via ``asyncio.create_task``.

If you wish to use background tasks it is best to use a task queue to
trigger background work, rather than spawn tasks in a view
function. With that in mind you can spawn asyncio tasks by serving
Flask with an ASGI server and utilising the asgiref WsgiToAsgi adapter
as described in :doc:`deploying/asgi`. This works as the adapter creates
an event loop that runs continually.


When to use Quart instead
-------------------------

Flask's async support is less performant than async-first frameworks due
to the way it is implemented. If you have a mainly async codebase it
would make sense to consider `Quart`_. Quart is a reimplementation of
Flask based on the `ASGI`_ standard instead of WSGI. This allows it to
handle many concurrent requests, long running requests, and websockets
without requiring multiple worker processes or threads.

It has also already been possible to run Flask with Gevent or Eventlet
to get many of the benefits of async request handling. These libraries
patch low-level Python functions to accomplish this, whereas ``async``/
``await`` and ASGI use standard, modern Python capabilities. Deciding
whether you should use Flask, Quart, or something else is ultimately up
to understanding the specific needs of your project.

.. _Quart: https://github.com/pallets/quart
.. _ASGI: https://asgi.readthedocs.io/en/latest/


Extensions
----------

Flask extensions predating Flask's async support do not expect async views.
If they provide decorators to add functionality to views, those will probably
not work with async views because they will not await the function or be
awaitable. Other functions they provide will not be awaitable either and
will probably be blocking if called within an async view.

Extension authors can support async functions by utilising the
:meth:`flask.Flask.ensure_sync` method. For example, if the extension
provides a view function decorator add ``ensure_sync`` before calling
the decorated function,

.. code-block:: python

    def extension(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ...  # Extension logic
            return current_app.ensure_sync(func)(*args, **kwargs)

        return wrapper

Check the changelog of the extension you want to use to see if they've
implemented async support, or make a feature request or PR to them.


Other event loops
-----------------

At the moment Flask only supports :mod:`asyncio`. It's possible to
override :meth:`flask.Flask.ensure_sync` to change how async functions
are wrapped to use a different library.
