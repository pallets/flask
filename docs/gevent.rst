Async with Gevent
=================

`Gevent`_ patches Python's standard library to run within special async workers
called `greenlets`_. Gevent has existed since long before Python's native
asyncio was available, and Flask has always worked with it.

.. _gevent: https://www.gevent.org
.. _greenlets: https://greenlet.readthedocs.io

Gevent is a reliable way to handle numerous, long lived, concurrent connections,
and to achieve similar capabilities to ASGI and asyncio. This works without
needing to write ``async def`` or ``await`` anywhere, but relies on gevent and
greenlet's low level manipulation of the Python interpreter.

Deciding whether you should use gevent with Flask, or `Quart`_, or something
else, is ultimately up to understanding the specific needs of your project.

.. _quart: https://quart.palletsprojects.com


Enabling gevent
---------------

You need to apply gevent's patching as early as possible in your code. This
enables gevent's underlying event loop and converts many Python internals to run
inside it. Add the following at the top of your project's module or top
``__init__.py``:

.. code-block:: python

    import gevent.monkey
    gevent.monkey.patch_all()

When deploying in production, use :doc:`/deploying/gunicorn` or
:doc:`/deploying/uwsgi` with a gevent worker, as described on those pages.

To run concurrent tasks within your own code, such as views, use
|gevent.spawn|_:

.. |gevent.spawn| replace:: ``gevent.spawn()``
.. _gevent.spawn: https://www.gevent.org/api/gevent.html#gevent.spawn

.. code-block:: python

    @app.post("/send")
    def send_email():
        gevent.spawn(email.send, to="example@example.example", text="example")
        return "Email is being sent."

If you need to access :data:`request` or other Flask context globals within the
spawned function, decorate the function with :func:`.stream_with_context` or
:func:`.copy_current_request_context`. Prefer passing the exact data you need
when spawning the function, rather than using the decorators.

.. note::

    When using gevent, greenlet>=1.0 is required. When using PyPy, PyPy>=7.3.7
    is required.


.. _gevent-asyncio:

Combining with ``async``/``await``
----------------------------------

Gevent's patching does not interact well with Flask's built-in asyncio support.
If you want to use Gevent and asyncio in the same app, you'll need to override
:meth:`flask.Flask.async_to_sync` to run async functions inside gevent.

.. code-block:: python

    import gevent.monkey
    gevent.monkey.patch_all()

    import asyncio
    from flask import Flask, request

    loop = asyncio.EventLoop()
    gevent.spawn(loop.run_forever)

    class GeventFlask(Flask):
        def async_to_sync(self, func):
            def run(*args, **kwargs):
                coro = func(*args, **kwargs)
                future = asyncio.run_coroutine_threadsafe(coro, loop)
                return future.result()

            return run

    app = GeventFlask(__name__)

    @app.get("/")
    async def greet():
        await asyncio.sleep(1)
        return f"Hello, {request.args.get("name", "World")}!"

This starts an asyncio event loop in a gevent worker. Async functions are
scheduled on that event loop. This may still have limitations, and may need to
be modified further when using other asyncio implementations.


libuv
~~~~~

`libuv`_ is another event loop implementation that `gevent supports`_. There's
also a project called `uvloop`_ that enables libuv in asyncio. If you want to
use libuv, use gevent's support, not uvloop. It may be possible to further
modify the ``async_to_sync`` code from the previous section to work with uvloop,
but that's not currently known.

.. _libuv: https://libuv.org/
.. _gevent supports: https://www.gevent.org/loop_impls.html
.. _uvloop: https://uvloop.readthedocs.io/

To enable gevent's libuv support, add the following at the *very* top of your
code, before ``gevent.monkey.patch_all()``:

.. code-block:: python

    import gevent
    gevent.config.loop = "libuv"

    import gevent.monkey
    gevent.monkey.patch_all()
