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

.. admonition:: Using ``async`` with greenlet

    When using gevent or eventlet to serve an application or patch the
    runtime, greenlet>=1.0 is required. When using PyPy, PyPy>=7.3.7 is
    required.

Async Views and gevent
----------------------

Flask supports defining async view functions using ``async def``, which are executed using
:mod:`asyncio`. When running Flask under a WSGI server, async views rely on an internal
bridge (``Flask.async_to_sync``) to integrate asyncio-based code into the synchronous request
lifecycle.

When using ``gevent``, especially with ``gevent.monkey.patch_all()``, there are important
limitations to be aware of.

Incompatibility with gevent monkey patching
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``gevent.monkey.patch_all()`` modifies parts of the Python standard library, including
threading and selectors, to use gevent’s cooperative greenlet-based scheduling. This
conflicts with assumptions made by :mod:`asyncio`, which expects a single event loop per
OS thread and threads created via :class:`threading.Thread` to be backed by real OS threads.

After monkey patching, threads may instead be implemented as greenlets running on the same
OS thread. Under concurrent requests, this can cause :mod:`asyncio` to detect multiple
event loops in the same thread, resulting in runtime errors such as::

    RuntimeError: You cannot use AsyncToSync in the same thread as an async event loop

This issue typically does not appear when handling a single request, but manifests under
concurrent load, which can make it difficult to detect during development.

Unsupported configuration
^^^^^^^^^^^^^^^^^^^^^^^^^

Running Flask async views together with gevent monkey patching is **not supported**. Even
in cases where simple async view functions appear to work, the behavior can be unreliable
and may break under concurrency, different event loop implementations (such as ``uvloop``),
or on different platforms.

Recommended alternatives
^^^^^^^^^^^^^^^^^^^^^^^^

If you are using gevent:

- Prefer synchronous Flask views when running under gevent
- Avoid ``gevent.monkey.patch_all()`` when using async views
- Consider using an ASGI server (such as ``uvicorn`` or ``hypercorn``) if you require
    asyncio-based concurrency

Advanced usage: overriding ``Flask.async_to_sync``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For advanced use cases, Flask allows overriding ``Flask.async_to_sync`` to customize how
async functions are executed. This can be used to experiment with alternative event loop
integrations, including gevent-based approaches.

Such configurations are highly environment-dependent and are not supported by Flask. Care
should be taken to fully understand the interaction between asyncio, gevent, and the chosen
event loop implementation.

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
