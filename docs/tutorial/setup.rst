.. _tutorial-setup:

Step 2: Application Setup Code
==============================

Now that we have the schema in place, we can create the application module.
Let's call it ``flaskr.py``. We will place this file inside the ``flaskr``
folder. We will begin by adding the imports we need and by adding the config
section.  For small applications, it is possible to drop the configuration
directly into the module, and this is what we will be doing here. However,
a cleaner solution would be to create a separate ``.ini`` or ``.py`` file,
load that, and import the values from there.

First, we add the imports in :file:`flaskr.py`::

    # all the imports
    import os
    import sqlite3
    from flask import Flask, request, session, g, redirect, url_for, abort, \
         render_template, flash

Next, we can create our actual application and initialize it with the
config from the same file in :file:`flaskr.py`::

    # create our little application :)
    app = Flask(__name__)
    app.config.from_object(__name__)

    # Load default config and override config from an environment variable
    app.config.update(dict(
        DATABASE=os.path.join(app.root_path, 'flaskr.db'),
        SECRET_KEY='development key',
        USERNAME='admin',
        PASSWORD='default'
    ))
    app.config.from_envvar('FLASKR_SETTINGS', silent=True)

The :class:`~flask.Config` object works similarly to a dictionary so we
can update it with new values.

.. admonition:: Database Path

    Operating systems know the concept of a current working directory for
    each process.  Unfortunately, you cannot depend on this in web
    applications because you might have more than one application in the
    same process.

    For this reason the ``app.root_path`` attribute can be used to
    get the path to the application.  Together with the ``os.path`` module,
    files can then easily be found.  In this example, we place the
    database right next to it.

    For a real-world application, it's recommended to use
    :ref:`instance-folders` instead.

Usually, it is a good idea to load a separate, environment-specific
configuration file.  Flask allows you to import multiple configurations and it
will use the setting defined in the last import. This enables robust
configuration setups.  :meth:`~flask.Config.from_envvar` can help achieve this.

.. code-block:: python

   app.config.from_envvar('FLASKR_SETTINGS', silent=True)

Simply define the environment variable :envvar:`FLASKR_SETTINGS` that points to
a config file to be loaded.  The silent switch just tells Flask to not complain
if no such environment key is set.

In addition to that, you can use the :meth:`~flask.Config.from_object`
method on the config object and provide it with an import name of a
module.  Flask will then initialize the variable from that module.  Note
that in all cases, only variable names that are uppercase are considered.

The ``SECRET_KEY`` is needed to keep the client-side sessions secure.
Choose that key wisely and as hard to guess and complex as possible.

We will also add a method that allows for easy connections to the
specified database. This can be used to open a connection on request and
also from the interactive Python shell or a script.  This will come in
handy later.  We create a simple database connection through SQLite and
then tell it to use the :class:`sqlite3.Row` object to represent rows.
This allows us to treat the rows as if they were dictionaries instead of
tuples.

::

    def connect_db():
        """Connects to the specific database."""
        rv = sqlite3.connect(app.config['DATABASE'])
        rv.row_factory = sqlite3.Row
        return rv

With that out of the way, you should be able to start up the application
without problems.  Do this with the following command::

    flask --app=flaskr --debug run

The :option:`--debug` flag enables or disables the interactive debugger.  *Never
leave debug mode activated in a production system*, because it will allow
users to execute code on the server!

You will see a message telling you that server has started along with
the address at which you can access it.

When you head over to the server in your browser, you will get a 404 error
because we don't have any views yet.  We will focus on that a little later,
but first, we should get the database working.

.. admonition:: Externally Visible Server

   Want your server to be publicly available?  Check out the
   :ref:`externally visible server <public-server>` section for more
   information.

Continue with :ref:`tutorial-dbcon`.
