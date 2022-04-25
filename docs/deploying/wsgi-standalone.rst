Standalone WSGI Servers
=======================

Most WSGI servers also provide HTTP servers, so they can run a WSGI
application and make it available externally.

It may still be a good idea to run the server behind a dedicated HTTP
server such as Apache or Nginx. See :ref:`deploying-proxy-setups` if you
run into issues with that.


Gunicorn
--------

`Gunicorn`_ is a WSGI and HTTP server for UNIX. To run a Flask
application, tell Gunicorn how to import your Flask app object.

.. code-block:: text

    $ gunicorn -w 4 -b 0.0.0.0:5000 your_project:app

The ``-w 4`` option uses 4 workers to handle 4 requests at once. The
``-b 0.0.0.0:5000`` serves the application on all interfaces on port
5000.

Gunicorn provides many options for configuring the server, either
through a configuration file or with command line options. Use
``gunicorn --help`` or see the docs for more information.

The command expects the name of your module or package to import and
the application instance within the module. If you use the application
factory pattern, you can pass a call to that.

.. code-block:: text

    $ gunicorn -w 4 -b 0.0.0.0:5000 "myproject:create_app()"


Async with Gevent or Eventlet
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The default sync worker is appropriate for many use cases. If you need
asynchronous support, Gunicorn provides workers using either `gevent`_
or `eventlet`_. This is not the same as Python's ``async/await``, or the
ASGI server spec.

When using either gevent or eventlet, greenlet>=1.0 is required,
otherwise context locals such as ``request`` will not work as expected.
When using PyPy, PyPy>=7.3.7 is required.

To use gevent:

.. code-block:: text

    $ gunicorn -k gevent -b 0.0.0.0:5000 your_project:app

To use eventlet:

.. code-block:: text

    $ gunicorn -k eventlet -b 0.0.0.0:5000 your_project:app


.. _Gunicorn: https://gunicorn.org/
.. _gevent: http://www.gevent.org/
.. _eventlet: https://eventlet.net/
.. _greenlet: https://greenlet.readthedocs.io/en/latest/


uWSGI
-----

`uWSGI`_ is a fast application server written in C. It is very
configurable, which makes it more complicated to setup than Gunicorn.
It also provides many other utilities for writing robust web
applications. To run a Flask application, tell uWSGI how to import
your Flask app object.

.. code-block:: text

    $ uwsgi --master -p 4 --http 0.0.0.0:5000 -w your_project:app

The ``-p 4`` option uses 4 workers to handle 4 requests at once. The
``--http 0.0.0.0:5000`` serves the application on all interfaces on port
5000.

uWSGI has optimized integration with Nginx and Apache instead of using
a standard HTTP proxy. See :doc:`configuring uWSGI and Nginx <uwsgi>`.


Async with Gevent
~~~~~~~~~~~~~~~~~

The default sync worker is appropriate for many use cases. If you need
asynchronous support, uWSGI provides workers using `gevent`_. It also
supports other async modes, see the docs for more information. This is
not the same as Python's ``async/await``, or the ASGI server spec.

When using gevent, greenlet>=1.0 is required, otherwise context locals
such as ``request`` will not work as expected. When using PyPy,
PyPy>=7.3.7 is required.

.. code-block:: text

    $ uwsgi --master --gevent 100 --http 0.0.0.0:5000 -w your_project:app

.. _uWSGI: https://uwsgi-docs.readthedocs.io/en/latest/


Gevent
------

Prefer using `Gunicorn`_ with Gevent workers rather than using Gevent
directly. Gunicorn provides a much more configurable and
production-tested server. See the section on Gunicorn above.

`Gevent`_ allows writing asynchronous, coroutine-based code that looks
like standard synchronous Python. It uses `greenlet`_ to enable task
switching without writing ``async/await`` or using ``asyncio``.

It provides a WSGI server that can handle many connections at once
instead of one per worker process.

`Eventlet`_, described below, is another library that does the same
thing. Certain dependencies you have, or other consideration, may affect
which of the two you choose to use

To use gevent to serve your application, import its ``WSGIServer`` and
use it to run your ``app``.

.. code-block:: python

    from gevent.pywsgi import WSGIServer
    from your_project import app

    http_server = WSGIServer(("", 5000), app)
    http_server.serve_forever()


Eventlet
--------

Prefer using `Gunicorn`_ with Eventlet workers rather than using
Eventlet directly. Gunicorn provides a much more configurable and
production-tested server. See the section on Gunicorn above.

`Eventlet`_ allows writing asynchronous, coroutine-based code that looks
like standard synchronous Python. It uses `greenlet`_ to enable task
switching without writing ``async/await`` or using ``asyncio``.

It provides a WSGI server that can handle many connections at once
instead of one per worker process.

`Gevent`_, described above, is another library that does the same
thing. Certain dependencies you have, or other consideration, may affect
which of the two you choose to use

To use eventlet to serve your application, import its ``wsgi.server``
and use it to run your ``app``.

.. code-block:: python

    import eventlet
    from eventlet import wsgi
    from your_project import app

    wsgi.server(eventlet.listen(("", 5000), app)


Twisted Web
-----------

`Twisted Web`_ is the web server shipped with `Twisted`_, a mature,
non-blocking event-driven networking library. Twisted Web comes with a
standard WSGI container which can be controlled from the command line using
the ``twistd`` utility:

.. code-block:: text

    $ twistd web --wsgi myproject.app

This example will run a Flask application called ``app`` from a module named
``myproject``.

Twisted Web supports many flags and options, and the ``twistd`` utility does
as well; see ``twistd -h`` and ``twistd web -h`` for more information. For
example, to run a Twisted Web server in the foreground, on port 8080, with an
application from ``myproject``:

.. code-block:: text

    $ twistd -n web --port tcp:8080 --wsgi myproject.app

.. _Twisted: https://twistedmatrix.com/trac/
.. _Twisted Web: https://twistedmatrix.com/trac/wiki/TwistedWeb


.. _deploying-proxy-setups:

Proxy Setups
------------

If you deploy your application using one of these servers behind an HTTP proxy
you will need to rewrite a few headers in order for the application to work.
The two problematic values in the WSGI environment usually are ``REMOTE_ADDR``
and ``HTTP_HOST``.  You can configure your httpd to pass these headers, or you
can fix them in middleware.  Werkzeug ships a fixer that will solve some common
setups, but you might want to write your own WSGI middleware for specific
setups.

Here's a simple nginx configuration which proxies to an application served on
localhost at port 8000, setting appropriate headers:

.. sourcecode:: nginx

    server {
        listen 80;

        server_name _;

        access_log  /var/log/nginx/access.log;
        error_log  /var/log/nginx/error.log;

        location / {
            proxy_pass         http://127.0.0.1:8000/;
            proxy_redirect     off;

            proxy_set_header   Host                 $host;
            proxy_set_header   X-Real-IP            $remote_addr;
            proxy_set_header   X-Forwarded-For      $proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Proto    $scheme;
        }
    }

If your httpd is not providing these headers, the most common setup invokes the
host being set from ``X-Forwarded-Host`` and the remote address from
``X-Forwarded-For``::

    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

.. admonition:: Trusting Headers

   Please keep in mind that it is a security issue to use such a middleware in
   a non-proxy setup because it will blindly trust the incoming headers which
   might be forged by malicious clients.

If you want to rewrite the headers from another header, you might want to
use a fixer like this::

    class CustomProxyFix(object):

        def __init__(self, app):
            self.app = app

        def __call__(self, environ, start_response):
            host = environ.get('HTTP_X_FHOST', '')
            if host:
                environ['HTTP_HOST'] = host
            return self.app(environ, start_response)

    app.wsgi_app = CustomProxyFix(app.wsgi_app)
