mod_wsgi
========

`mod_wsgi`_ is a WSGI server integrated with the `Apache httpd`_ server.
The modern `mod_wsgi-express`_ command makes it easy to configure and
start the server without needing to write Apache httpd configuration.

*   Tightly integrated with Apache httpd.
*   Supports Windows directly.
*   Requires a compiler and the Apache development headers to install.
*   Does not require a reverse proxy setup.

This page outlines the basics of running mod_wsgi-express, not the more
complex installation and configuration with httpd. Be sure to read the
`mod_wsgi-express`_, `mod_wsgi`_, and `Apache httpd`_ documentation to
understand what features are available.

.. _mod_wsgi-express: https://pypi.org/project/mod-wsgi/
.. _mod_wsgi: https://modwsgi.readthedocs.io/
.. _Apache httpd: https://httpd.apache.org/


Installing
----------

Installing mod_wsgi requires a compiler and the Apache server and
development headers installed. You will get an error if they are not.
How to install them depends on the OS and package manager that you use.

Create a virtualenv, install your application, then install
``mod_wsgi``.

.. code-block:: text

    $ cd hello-app
    $ python -m venv venv
    $ . venv/bin/activate
    $ pip install .  # install your application
    $ pip install mod_wsgi


Running
-------

The only argument to ``mod_wsgi-express`` specifies a script containing
your Flask application, which must be called ``application``. You can
write a small script to import your app with this name, or to create it
if using the app factory pattern.

.. code-block:: python
    :caption: ``wsgi.py``

    from hello import app

    application = app

.. code-block:: python
    :caption: ``wsgi.py``

    from hello import create_app

    application = create_app()

Now run the ``mod_wsgi-express start-server`` command.

.. code-block:: text

    $ mod_wsgi-express start-server wsgi.py --processes 4

The ``--processes`` option specifies the number of worker processes to
run; a starting value could be ``CPU * 2``.

Logs for each request aren't show in the terminal. If an error occurs,
its information is written to the error log file shown when starting the
server.


Binding Externally
------------------

Unlike the other WSGI servers in these docs, mod_wsgi can be run as
root to bind to privileged ports like 80 and 443. However, it must be
configured to drop permissions to a different user and group for the
worker processes.

For example, if you created a ``hello`` user and group, you should
install your virtualenv and application as that user, then tell
mod_wsgi to drop to that user after starting.

.. code-block:: text

    $ sudo /home/hello/venv/bin/mod_wsgi-express start-server \
        /home/hello/wsgi.py \
        --user hello --group hello --port 80 --processes 4
