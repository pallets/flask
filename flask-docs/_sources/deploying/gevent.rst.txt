gevent
======

Prefer using :doc:`gunicorn` or :doc:`uwsgi` with gevent workers rather
than using `gevent`_ directly. Gunicorn and uWSGI provide much more
configurable and production-tested servers.

`gevent`_ allows writing asynchronous, coroutine-based code that looks
like standard synchronous Python. It uses `greenlet`_ to enable task
switching without writing ``async/await`` or using ``asyncio``.

:doc:`eventlet` is another library that does the same thing. Certain
dependencies you have, or other considerations, may affect which of the
two you choose to use.

gevent provides a WSGI server that can handle many connections at once
instead of one per worker process. You must actually use gevent in your
own code to see any benefit to using the server.

.. _gevent: https://www.gevent.org/
.. _greenlet: https://greenlet.readthedocs.io/en/latest/


Installing
----------

When using gevent, greenlet>=1.0 is required, otherwise context locals
such as ``request`` will not work as expected. When using PyPy,
PyPy>=7.3.7 is required.

Create a virtualenv, install your application, then install ``gevent``.

.. code-block:: text

    $ cd hello-app
    $ python -m venv .venv
    $ . .venv/bin/activate
    $ pip install .  # install your application
    $ pip install gevent


Running
-------

To use gevent to serve your application, write a script that imports its
``WSGIServer``, as well as your app or app factory.

.. code-block:: python
    :caption: ``wsgi.py``

    from gevent.pywsgi import WSGIServer
    from hello import create_app

    app = create_app()
    http_server = WSGIServer(("127.0.0.1", 8000), app)
    http_server.serve_forever()

.. code-block:: text

    $ python wsgi.py

No output is shown when the server starts.


Binding Externally
------------------

gevent should not be run as root because it would cause your
application code to run as root, which is not secure. However, this
means it will not be possible to bind to port 80 or 443. Instead, a
reverse proxy such as :doc:`nginx` or :doc:`apache-httpd` should be used
in front of gevent.

You can bind to all external IPs on a non-privileged port by using
``0.0.0.0`` in the server arguments shown in the previous section. Don't
do this when using a reverse proxy setup, otherwise it will be possible
to bypass the proxy.

``0.0.0.0`` is not a valid address to navigate to, you'd use a specific
IP address in your browser.
