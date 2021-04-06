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


When to use Quart instead
-------------------------

Flask's async support is less performant than async-first frameworks due
to the way it is implemented. If you have a mainly async codebase it
would make sense to consider `Quart`_. Quart is a reimplementation of
Flask based on the `ASGI`_ standard instead of WSGI. This allows it to
handle many concurrent requests, long running requests, and websockets
without requiring individual worker processes or threads.

It has also already been possible to run Flask with Gevent or Eventlet
to get many of the benefits of async request handling. These libraries
patch low-level Python functions to accomplish this, whereas ``async``/
``await`` and ASGI use standard, modern Python capabilities. Deciding
whether you should use Flask, Quart, or something else is ultimately up
to understanding the specific needs of your project.

.. _Quart: https://gitlab.com/pgjones/quart
.. _ASGI: https://asgi.readthedocs.io/en/latest/


Extensions
----------

Existing Flask extensions only expect views to be synchronous. If they
provide decorators to add functionality to views, those will probably
not work with async views because they will not await the function or be
awaitable. Other functions they provide will not be awaitable either and
will probably be blocking if called within an async view.

Check the changelog of the extension you want to use to see if they've
implemented async support, or make a feature request or PR to them.


Other event loops
-----------------

At the moment Flask only supports :mod:`asyncio`. It's possible to
override :meth:`flask.Flask.ensure_sync` to change how async functions
are wrapped to use a different library.
