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

After installation of Flask you will now find a :command:`flask` script installed
into your virtualenv.  If you don't want to install Flask or you have a
special use-case you can also use ``python -m flask`` to accomplish exactly
the same.

The way this script works is by providing access to all the commands on
your Flask application's :attr:`Flask.cli` instance as well as some
built-in commands that are always there.  Flask extensions can also
register more commands there if they desire so.

For the :command:`flask` script to work, an application needs to be discovered.
The two most common ways are either an environment variable
(``FLASK_APP``) or the :option:`--app` / :option:`-a` parameter.  It should be the
import path for your application or the path to a Python file.  In the
latter case Flask will attempt to setup the Python path for you
automatically and discover the module name but that might not always work.

In that imported file the name of the app needs to be called ``app`` or
optionally be specified after a colon.

Given a :file:`hello.py` file with the application in it named ``app`` this is
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

The :command:`flask` script can be run with :option:`--debug` or :option:`--no-debug` to
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
:ref:`app-factories`) you will discover that the :command:`flask` command cannot
work with them directly.  Flask won't be able to figure out how to
instantiate your application properly by itself.  Because of this reason
the recommendation is to create a separate file that instantiates
applications.  This is by far not the only way to make this work.  Another
is the :ref:`custom-scripts` support.

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

While the most common way is to use the :command:`flask` command, you can also
make your own "driver scripts".  Since Flask uses click for the scripts
there is no reason you cannot hook these scripts into any click
application.  There is one big caveat and that is, that commands
registered to :attr:`Flask.cli` will expect to be (indirectly at least)
launched from a :class:`flask.cli.FlaskGroup` click group.  This is
necessary so that the commands know which Flask application they have to
work with.

To understand why you might want custom scripts you need to understand how
click finds and executes the Flask application.  If you use the :command:`flask`
script you specify the application to work with on the command line or
environment variable as an import name.  This is simple but it has some
limitations.  Primarily it does not work with application factory
functions (see :ref:`app-factories`).

With a custom script you don't have this problem as you can fully
customize how the application will be created.  This is very useful if you
write reusable applications that you want to ship to users and they should
be presented with a custom management script.

If you are used to writing click applications this will look familiar but
at the same time, slightly different because of how commands are loaded.
We won't go into detail now about the differences but if you are curious
you can have a look at the :ref:`script-info-object` section to learn all
about it.

To explain all of this, here is an example :file:`manage.py` script that
manages a hypothetical wiki application.  We will go through the details
afterwards::

    import click
    from flask.cli import FlaskGroup, script_info_option

    def create_wiki_app(info):
        from yourwiki import create_app
        config = info.data.get('config') or 'wikiconfig.py'
        return create_app(config=config)

    @click.group(cls=FlaskGroup, create_app=create_wiki_app)
    @script_info_option('--config', script_info_key='config')
    def cli(**params):
        """This is a management script for the wiki application."""

    if __name__ == '__main__':
        cli()

That's a lot of code for not much, so let's go through all parts step by
step.

1.  First we import the ``click`` library as well as the click extensions
    from the ``flask.cli`` package.  Primarily we are here interested
    in the :class:`~flask.cli.FlaskGroup` click group and the
    :func:`~flask.cli.script_info_option` decorator.
2.  The next thing we do is defining a function that is invoked with the
    script info object (:ref:`script-info-object`) from Flask and its
    purpose is to fully import and create the application.  This can
    either directly import an application object or create it (see
    :ref:`app-factories`).

    What is ``info.data``?  It's a dictionary of arbitrary data on the
    script info that can be filled by options or through other means.  We
    will come back to this later.
3.  Next step is to create a :class:`FlaskGroup`.  In this case we just
    make an empty function with a help doc string that just does nothing
    and then pass the ``create_wiki_app`` function as a factory function.

    Whenever click now needs to operate on a Flask application it will
    call that function with the script info and ask for it to be created.
4.  In step 2 you could see that the config is passed to the actual
    creation function.  This config comes from the :func:`script_info_option`
    decorator for the main script.  It accepts a :option:`--config` option and
    then stores it in the script info so we can use it to create the
    application.
5.  All is rounded up by invoking the script.

.. _script-info-object:

The Script Info
---------------

The Flask script integration might be confusing at first, but there is a reason
why it's done this way.  The reason for this is that Flask wants to
both provide custom commands to click as well as not loading your
application unless it has to.  The reason for this is added flexibility.

This way an application can provide custom commands, but even in the
absence of an application the :command:`flask` script is still operational on a
basic level.  In addition to that it means that the individual commands
have the option to avoid creating an instance of the Flask application
unless required.  This is very useful as it allows the server commands for
instance to load the application on a first request instead of
immediately, therefore giving a better debug experience.

All of this is provided through the :class:`flask.cli.ScriptInfo` object
and some helper utilities around.  The basic way it operates is that when
the :class:`flask.cli.FlaskGroup` executes as a script it creates a script
info and keeps it around.  From that point onwards modifications on the
script info can be done through click options.  To simplify this pattern
the :func:`flask.cli.script_info_option` decorator was added.

Once Flask actually needs the individual Flask application it will invoke
the :meth:`flask.cli.ScriptInfo.load_app` method.  This happens when the
server starts, when the shell is launched or when the script looks for an
application-provided click command.
