uWSGI
=====

`uWSGI`_ is a fast, compiled server suite with extensive configuration
and capabilities beyond a basic server.

*   It can be very performant due to being a compiled program.
*   It is complex to configure beyond the basic application, and has so
    many options that it can be difficult for beginners to understand.
*   It does not support Windows (but does run on WSL).
*   It requires a compiler to install in some cases.

This page outlines the basics of running uWSGI. Be sure to read its
documentation to understand what features are available.

.. _uWSGI: https://uwsgi-docs.readthedocs.io/en/latest/


Installing
----------

uWSGI has multiple ways to install it. The most straightforward is to
install the ``pyuwsgi`` package, which provides precompiled wheels for
common platforms. However, it does not provide SSL support, which can be
provided with a reverse proxy instead.

Create a virtualenv, install your application, then install ``pyuwsgi``.

.. code-block:: text

    $ cd hello-app
    $ python -m venv venv
    $ . venv/bin/activate
    $ pip install .  # install your application
    $ pip install pyuwsgi

If you have a compiler available, you can install the ``uwsgi`` package
instead. Or install the ``pyuwsgi`` package from sdist instead of wheel.
Either method will include SSL support.

.. code-block:: text

    $ pip install uwsgi

    # or
    $ pip install --no-binary pyuwsgi pyuwsgi


Running
-------

The most basic way to run uWSGI is to tell it to start an HTTP server
and import your application.

.. code-block:: text

    $ uwsgi --http 127.0.0.1:8000 --master -p 4 -w hello:app

    *** Starting uWSGI 2.0.20 (64bit) on [x] ***
    *** Operational MODE: preforking ***
    mounting hello:app on /
    spawned uWSGI master process (pid: x)
    spawned uWSGI worker 1 (pid: x, cores: 1)
    spawned uWSGI worker 2 (pid: x, cores: 1)
    spawned uWSGI worker 3 (pid: x, cores: 1)
    spawned uWSGI worker 4 (pid: x, cores: 1)
    spawned uWSGI http 1 (pid: x)

If you're using the app factory pattern, you'll need to create a small
Python file to create the app, then point uWSGI at that.

.. code-block:: python
    :caption: ``wsgi.py``

    from hello import create_app

    app = create_app()

.. code-block:: text

    $ uwsgi --http 127.0.0.1:8000 --master -p 4 -w wsgi:app

The ``--http`` option starts an HTTP server at 127.0.0.1 port 8000. The
``--master`` option specifies the standard worker manager. The ``-p``
option starts 4 worker processes; a starting value could be ``CPU * 2``.
The ``-w`` option tells uWSGI how to import your application


Binding Externally
------------------

uWSGI should not be run as root with the configuration shown in this doc
because it would cause your application code to run as root, which is
not secure. However, this means it will not be possible to bind to port
80 or 443. Instead, a reverse proxy such as :doc:`nginx` or
:doc:`apache-httpd` should be used in front of uWSGI. It is possible to
run uWSGI as root securely, but that is beyond the scope of this doc.

uWSGI has optimized integration with `Nginx uWSGI`_ and
`Apache mod_proxy_uwsgi`_, and possibly other servers, instead of using
a standard HTTP proxy. That configuration is beyond the scope of this
doc, see the links for more information.

.. _Nginx uWSGI: https://uwsgi-docs.readthedocs.io/en/latest/Nginx.html
.. _Apache mod_proxy_uwsgi: https://uwsgi-docs.readthedocs.io/en/latest/Apache.html#mod-proxy-uwsgi

You can bind to all external IPs on a non-privileged port using the
``--http 0.0.0.0:8000`` option. Don't do this when using a reverse proxy
setup, otherwise it will be possible to bypass the proxy.

.. code-block:: text

    $ uwsgi --http 0.0.0.0:8000 --master -p 4 -w wsgi:app

``0.0.0.0`` is not a valid address to navigate to, you'd use a specific
IP address in your browser.


Async with gevent
-----------------

The default sync worker is appropriate for many use cases. If you need
asynchronous support, uWSGI provides a `gevent`_ worker. This is not the
same as Python's ``async/await``, or the ASGI server spec. You must
actually use gevent in your own code to see any benefit to using the
worker.

When using gevent, greenlet>=1.0 is required, otherwise context locals
such as ``request`` will not work as expected. When using PyPy,
PyPy>=7.3.7 is required.

.. code-block:: text

    $ uwsgi --http 127.0.0.1:8000 --master --gevent 100 -w wsgi:app

    *** Starting uWSGI 2.0.20 (64bit) on [x] ***
    *** Operational MODE: async ***
    mounting hello:app on /
    spawned uWSGI master process (pid: x)
    spawned uWSGI worker 1 (pid: x, cores: 100)
    spawned uWSGI http 1 (pid: x)
    *** running gevent loop engine [addr:x] ***


.. _gevent: https://www.gevent.org/
