.. currentmodule:: flask

Development Server
==================

Flask provides a ``run`` command to run the application with a development server. In
debug mode, this server provides an interactive debugger and will reload when code is
changed.

.. warning::

    Do not use the development server when deploying to production. It
    is intended for use only during local development. It is not
    designed to be particularly efficient, stable, or secure.

    See :doc:`/deploying/index` for deployment options.

Command Line
------------

The ``flask run`` CLI command is the recommended way to run the development server. Use
the ``--app`` option to point to your application, and the ``--debug`` option to enable
debug mode.

.. code-block:: text

    $ flask --app hello --debug run

This enables debug mode, including the interactive debugger and reloader, and then
starts the server on http://localhost:5000/. Use ``flask run --help`` to see the
available options, and :doc:`/cli` for detailed instructions about configuring and using
the CLI.


.. _address-already-in-use:

Address already in use
~~~~~~~~~~~~~~~~~~~~~~

If another program is already using port 5000, you'll see an ``OSError``
when the server tries to start. It may have one of the following
messages:

-   ``OSError: [Errno 98] Address already in use``
-   ``OSError: [WinError 10013] An attempt was made to access a socket
    in a way forbidden by its access permissions``

Either identify and stop the other program, or use
``flask run --port 5001`` to pick a different port.

You can use ``netstat`` or ``lsof`` to identify what process id is using
a port, then use other operating system tools stop that process. The
following example shows that process id 6847 is using port 5000.

.. tabs::

    .. tab:: ``netstat`` (Linux)

        .. code-block:: text

            $ netstat -nlp | grep 5000
            tcp 0 0 127.0.0.1:5000 0.0.0.0:* LISTEN 6847/python

    .. tab:: ``lsof`` (macOS / Linux)

        .. code-block:: text

            $ lsof -P -i :5000
            Python 6847 IPv4 TCP localhost:5000 (LISTEN)

    .. tab:: ``netstat`` (Windows)

        .. code-block:: text

            > netstat -ano | findstr 5000
            TCP 127.0.0.1:5000 0.0.0.0:0 LISTENING 6847

macOS Monterey and later automatically starts a service that uses port
5000. To disable the service, go to System Preferences, Sharing, and
disable "AirPlay Receiver".


Deferred Errors on Reload
~~~~~~~~~~~~~~~~~~~~~~~~~

When using the ``flask run`` command with the reloader, the server will
continue to run even if you introduce syntax errors or other
initialization errors into the code. Accessing the site will show the
interactive debugger for the error, rather than crashing the server.

If a syntax error is already present when calling ``flask run``, it will
fail immediately and show the traceback rather than waiting until the
site is accessed. This is intended to make errors more visible initially
while still allowing the server to handle errors on reload.


In Code
-------

The development server can also be started from Python with the :meth:`Flask.run`
method. This method takes arguments similar to the CLI options to control the server.
The main difference from the CLI command is that the server will crash if there are
errors when reloading. ``debug=True`` can be passed to enable debug mode.

Place the call in a main block, otherwise it will interfere when trying to import and
run the application with a production server later.

.. code-block:: python

    if __name__ == "__main__":
        app.run(debug=True)

.. code-block:: text

    $ python hello.py
