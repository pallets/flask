eventlet
========

Prefer using :doc:`gunicorn` with eventlet workers rather than using
`eventlet`_ directly. Gunicorn provides a much more configurable and
production-tested server.

`eventlet`_ allows writing asynchronous, coroutine-based code that looks
like standard synchronous Python. It uses `greenlet`_ to enable task
switching without writing ``async/await`` or using ``asyncio``.

:doc:`gevent` is another library that does the same thing. Certain
dependencies you have, or other considerations, may affect which of the
two you choose to use.

eventlet provides a WSGI server that can handle many connections at once
instead of one per worker process. You must actually use eventlet in
your own code to see any benefit to using the server.

.. _eventlet: https://eventlet.net/
.. _greenlet: https://greenlet.readthedocs.io/en/latest/


Installing
----------

When using eventlet, greenlet>=1.0 is required, otherwise context locals
such as ``request`` will not work as expected. When using PyPy,
PyPy>=7.3.7 is required.

Create a virtualenv, install your application, then install
``eventlet``.

.. code-block:: text

    $ cd hello-app
    $ python -m venv .venv
    $ . .venv/bin/activate
    $ pip install .  # install your application
    $ pip install eventlet


Running
-------

To use eventlet to serve your application, write a script that imports
its ``wsgi.server``, as well as your app or app factory.

.. code-block:: python
    :caption: ``wsgi.py``

    import eventlet
    from eventlet import wsgi
    from hello import create_app

    app = create_app()
    wsgi.server(eventlet.listen(("127.0.0.1", 8000)), app)

.. code-block:: text

    $ python wsgi.py
    (x) wsgi starting up on http://127.0.0.1:8000


Binding Externally
------------------

eventlet should not be run as root because it would cause your
application code to run as root, which is not secure. However, this
means it will not be possible to bind to port 80 or 443. Instead, a
reverse proxy such as :doc:`nginx` or :doc:`apache-httpd` should be used
in front of eventlet.

You can bind to all external IPs on a non-privileged port by using
``0.0.0.0`` in the server arguments shown in the previous section.
Don't do this when using a reverse proxy setup, otherwise it will be
possible to bypass the proxy.

``0.0.0.0`` is not a valid address to navigate to, you'd use a specific
IP address in your browser.
