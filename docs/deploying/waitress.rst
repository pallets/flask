Waitress
========

`Waitress`_ is a pure Python WSGI server.

*   It is easy to configure.
*   It supports Windows directly.
*   It is easy to install as it does not require additional dependencies
    or compilation.
*   It does not support streaming requests, full request data is always
    buffered.
*   It uses a single process with multiple thread workers.

This page outlines the basics of running Waitress. Be sure to read its
documentation and ``waitress-serve --help`` to understand what features
are available.

.. _Waitress: https://docs.pylonsproject.org/projects/waitress/


Installing
----------

Create a virtualenv, install your application, then install
``waitress``.

.. code-block:: text

    $ cd hello-app
    $ python -m venv .venv
    $ . .venv/bin/activate
    $ pip install .  # install your application
    $ pip install waitress


Running
-------

The only required argument to ``waitress-serve`` tells it how to load
your Flask application. The syntax is ``{module}:{app}``. ``module`` is
the dotted import name to the module with your application. ``app`` is
the variable with the application. If you're using the app factory
pattern, use ``--call {module}:{factory}`` instead.

.. code-block:: text

    # equivalent to 'from hello import app'
    $ waitress-serve --host 127.0.0.1 hello:app

    # equivalent to 'from hello import create_app; create_app()'
    $ waitress-serve --host 127.0.0.1 --call hello:create_app

    Serving on http://127.0.0.1:8080

The ``--host`` option binds the server to local ``127.0.0.1`` only.

Logs for each request aren't shown, only errors are shown. Logging can
be configured through the Python interface instead of the command line.


Binding Externally
------------------

Waitress should not be run as root because it would cause your
application code to run as root, which is not secure. However, this
means it will not be possible to bind to port 80 or 443. Instead, a
reverse proxy such as :doc:`nginx` or :doc:`apache-httpd` should be used
in front of Waitress.

You can bind to all external IPs on a non-privileged port by not
specifying the ``--host`` option. Don't do this when using a revers
proxy setup, otherwise it will be possible to bypass the proxy.

``0.0.0.0`` is not a valid address to navigate to, you'd use a specific
IP address in your browser.
