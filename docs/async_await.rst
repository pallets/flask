.. _async_await:

Using async and await
=====================

.. versionadded:: 2.0

Routes, error handlers, before request, after request, and teardown
functions can all be coroutine functions if Flask is installed with
the ``async`` extra (``pip install flask[async]``). This allows code
such as,

.. code-block:: python

    @app.route("/")
    async def index():
        return await ...

including the usage of any asyncio based libraries.


When to use Quart instead
-------------------------

Flask's ``async/await`` support is less performant than async first
frameworks due to the way it is implemented. Therefore if you have a
mainly async codebase it would make sense to consider `Quart
<https://gitlab.com/pgjones/quart>`_. Quart is a reimplementation of
the Flask using ``async/await`` based on the ASGI standard (Flask is
based on the WSGI standard).


Decorators
----------

Decorators designed for Flask, such as those in Flask extensions are
unlikely to work. This is because the decorator will not await the
coroutine function nor will they themselves be awaitable.


Other event loops
-----------------

At the moment Flask only supports asyncio - the
:meth:`flask.Flask.ensure_sync` should be overridden to support
alternative event loops.
