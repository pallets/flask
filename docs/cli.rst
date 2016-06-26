.. _cli:

Command Line Interface
======================

.. versionadded:: 0.11

.. currentmodule:: flask

One of the nice new features in Flask 0.11 is the built-in integration of
the `click <http://click.pocoo.org/>`_ command line interface.  This
enables a wide range of new features for the Flask ecosystem and your own
applications.

Basic Usage
-----------

After installation of Flask you will now find a :command:`flask` script
installed into your virtualenv.  If you don't want to install Flask or you
have a special use-case you can also use ``python -m flask`` to accomplish
exactly the same.

The way this script works is by providing access to all the commands on
your Flask application's :attr:`Flask.cli` instance as well as some
built-in commands that are always there.  Flask extensions can also
register more commands there if they desire so.

For the :command:`flask` script to work, an application needs to be
discovered.  This is achieved by exporting the ``FLASK_APP`` environment
variable.  It can be either set to an import path or to a filename of a
Python module that contains a Flask application.

In that imported file the name of the app needs to be called ``app`` or
optionally be specified after a colon.  For instance
``mymodule:application`` would tell it to use the `application` object in
the :file:`mymodule.py` file.

Given a :file:`hello.py` file with the application in it named ``app``
this is how it can be run.

Environment variables (On Windows use ``set`` instead of ``export``)::

    export FLASK_APP=hello
    flask run

Or with a filename::

    export FLASK_APP=/path/to/hello.py
    flask run

Virtualenv Integration
----------------------

If you are constantly working with a virtualenv you can also put the
``export FLASK_APP`` into your ``activate`` script by adding it to the
bottom of the file.  That way every time you activate your virtualenv you
automatically also activate the correct application name.

Debug Flag
----------

The :command:`flask` script can also be instructed to enable the debug
mode of the application automatically by exporting ``FLASK_DEBUG``.  If
set to ``1`` debug is enabled or ``0`` disables it.

Or with a filename::

    export FLASK_DEBUG=1

Running a Shell
---------------

To run an interactive Python shell you can use the ``shell`` command::

    flask shell

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

    import click
    from flask import Flask

    app = Flask(__name__)

    @app.cli.command()
    def initdb():
        """Initialize the database."""
        click.echo('Init the db')

The command will then show up on the command line::

    $ flask initdb
    Init the db

Application Context
-------------------

Most commands operate on the application so it makes a lot of sense if
they have the application context setup.  Because of this, if you register
a callback on ``app.cli`` with the :meth:`~flask.cli.AppGroup.command` the
callback will automatically be wrapped through :func:`cli.with_appcontext`
which informs the cli system to ensure that an application context is set
up.  This behavior is not available if a command is added later with
:func:`~click.Group.add_command` or through other means.

It can also be disabled by passing ``with_appcontext=False`` to the
decorator::

    @app.cli.command(with_appcontext=False)
    def example():
        pass

Factory Functions
-----------------

In case you are using factory functions to create your application (see
:ref:`app-factories`) you will discover that the :command:`flask` command
cannot work with them directly.  Flask won't be able to figure out how to
instantiate your application properly by itself.  Because of this reason
the recommendation is to create a separate file that instantiates
applications.  This is not the only way to make this work.  Another is the
:ref:`custom-scripts` support.

For instance if you have a factory function that creates an application
from a filename you could make a separate file that creates such an
application from an environment variable.

This could be a file named :file:`autoapp.py` with these contents::

    import os
    from yourapplication import create_app
    app = create_app(os.environ['YOURAPPLICATION_CONFIG'])

Once this has happened you can make the flask command automatically pick
it up::

    export YOURAPPLICATION_CONFIG=/path/to/config.cfg
    export FLASK_APP=/path/to/autoapp.py

From this point onwards :command:`flask` will find your application.

.. _custom-scripts:

Custom Scripts
--------------

While the most common way is to use the :command:`flask` command, you can
also make your own "driver scripts".  Since Flask uses click for the
scripts there is no reason you cannot hook these scripts into any click
application.  There is one big caveat and that is, that commands
registered to :attr:`Flask.cli` will expect to be (indirectly at least)
launched from a :class:`flask.cli.FlaskGroup` click group.  This is
necessary so that the commands know which Flask application they have to
work with.

To understand why you might want custom scripts you need to understand how
click finds and executes the Flask application.  If you use the
:command:`flask` script you specify the application to work with on the
command line or environment variable as an import name.  This is simple
but it has some limitations.  Primarily it does not work with application
factory functions (see :ref:`app-factories`).

With a custom script you don't have this problem as you can fully
customize how the application will be created.  This is very useful if you
write reusable applications that you want to ship to users and they should
be presented with a custom management script.

To explain all of this, here is an example :file:`manage.py` script that
manages a hypothetical wiki application.  We will go through the details
afterwards::

    import os
    import click
    from flask.cli import FlaskGroup

    def create_wiki_app(info):
        from yourwiki import create_app
        return create_app(
            config=os.environ.get('WIKI_CONFIG', 'wikiconfig.py'))

    @click.group(cls=FlaskGroup, create_app=create_wiki_app)
    def cli():
        """This is a management script for the wiki application."""

    if __name__ == '__main__':
        cli()

That's a lot of code for not much, so let's go through all parts step by
step.

1.  First we import the ``click`` library as well as the click extensions
    from the ``flask.cli`` package.  Primarily we are here interested
    in the :class:`~flask.cli.FlaskGroup` click group.
2.  The next thing we do is defining a function that is invoked with the
    script info object (:class:`~flask.cli.ScriptInfo`) from Flask and its
    purpose is to fully import and create the application.  This can
    either directly import an application object or create it (see
    :ref:`app-factories`).  In this case we load the config from an
    environment variable.
3.  Next step is to create a :class:`FlaskGroup`.  In this case we just
    make an empty function with a help doc string that just does nothing
    and then pass the ``create_wiki_app`` function as a factory function.

    Whenever click now needs to operate on a Flask application it will
    call that function with the script info and ask for it to be created.
4.  All is rounded up by invoking the script.

CLI Plugins
-----------

Flask extensions can always patch the :attr:`Flask.cli` instance with more
commands if they want.  However there is a second way to add CLI plugins
to Flask which is through ``setuptools``.  If you make a Python package that
should export a Flask command line plugin you can ship a :file:`setup.py` file
that declares an entrypoint that points to a click command:

Example :file:`setup.py`::

    from setuptools import setup

    setup(
        name='flask-my-extension',
        ...
        entry_points='''
            [flask.commands]
            my-command=mypackage.commands:cli
        ''',
    )

Inside :file:`mypackage/commands.py` you can then export a Click object::

    import click

    @click.command()
    def cli():
        """This is an example command."""

Once that package is installed in the same virtualenv as Flask itself you
can run ``flask my-command`` to invoke your command.  This is useful to
provide extra functionality that Flask itself cannot ship.
