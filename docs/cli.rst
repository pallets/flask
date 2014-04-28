.. _cli:

Command Line Interface
======================

.. versionadded:: 1.0

.. currentmodule:: flask

One of the nice new features in Flask 1.0 is the built-in integration of
the `click <http://click.pocoo.org/>`_ command line interface.  This
enables a wide range of new features for the Flask ecosystem and your own
applications.

Basic Usage
-----------

After installation of Flask you will now find a ``flask`` script installed
into your virtualenv.  If you don't want to install Flask or you have a
special use-case you can also use ``python -mflask`` to accomplish exactly
the same.

The way this script works is by providing access to all the commands on
your Flask application's :attr:`Flask.cli` instance as well as some
built-in commands that are always there.  Flask extensions can also
register more commands there if they so desire.

For the ``flask`` script to work, an application needs to be discovered.
The two most common ways are either an environment variable
(``FLASK_APP``) or the ``--app`` / ``-a`` parameter.  It should be the
import path for your application or the path to a Python file.  In the
latter case Flask will attempt to setup the Python path for you
automatically and discover the module name but that might not always work.

In that imported file the name of the app needs to be called ``app`` or
optionally be specified after a colon.

Given a ``hello.py`` file with the application in it named ``app`` this is
how it can be run.

Environment variables (On Windows use ``set`` instead of ``export``)::

    export FLASK_APP=hello
    flask run

Parameters::

    flask --app=hello run

File names::

    flask --app=hello.py run

Virtualenv Integration
----------------------

If you are constantly working with a virtualenv you can also put the
``export FLASK_APP`` into your ``activate`` script by adding it to the
bottom of the file.  That way every time you activate your virtualenv you
automatically also activate the correct application name.

Debug Flag
----------

The ``flask`` script can be run with ``--debug`` or ``--no-debug`` to
automatically flip the debug flag of the application.  This can also be
configured by setting ``FLASK_DEBUG`` to ``1`` or ``0``.

Running a Shell
---------------

To run an interactive Python shell you can use the ``shell`` command::

    flask --app=hello shell

This will start up an interactive Python shell, setup the correct
application context and setup the local variables in the shell.  This is
done by invoking the :meth:`Flask.make_shell_context` method of the
application.  By default you have access to your ``app`` and :data:`g`.

Custom Commands
---------------

If you want to add more commands to the shell script you can do this
easily.  Flask uses `click`_ for the command interface which makes
creating custom commands very easy.  For instance if you want a shell
command to initialize the database you can do this::

    from flask import Flask

    app = Flask(__name__)

    @app.cli.command()
    def initdb():
        """Initialize the database."""
        print 'Init the db'

The command will then show up on the command line::

    $ flask -a hello.py initdb
    Init the db
