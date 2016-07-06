.. _tutorial-setup:

Step 2: Application Setup Code
==============================

Now that the schema is in place, you can create the application module,
:file:`flaskr.py`.  This file should be placed inside of the
:file:`flaskr/flaskr` folder.  The first several lines of code in the
application module are the needed import statements.  After that there will be a
few lines of configuration code. For small applications like ``flaskr``, it is
possible to drop the configuration directly into the module.  However, a cleaner
solution is to create a separate ``.ini`` or ``.py`` file, load that, and
import the values from there.

Here are the import statements (in :file:`flaskr.py`)::

    # all the imports
    import os
    import sqlite3
    from flask import Flask, request, session, g, redirect, url_for, abort, \
         render_template, flash

The next couple lines will create the actual application instance and
initialize it with the config from the same file in :file:`flaskr.py`:

.. sourcecode:: python

    app = Flask(__name__) # create the application instance :)
    app.config.from_object(__name__) # load config from this file , flaskr.py

    # Load default config and override config from an environment variable
    app.config.update(dict(
        DATABASE=os.path.join(app.root_path, 'flaskr.db'),
        SECRET_KEY='development key',
        USERNAME='admin',
        PASSWORD='default'
    ))
    app.config.from_envvar('FLASKR_SETTINGS', silent=True)

The :class:`~flask.Config` object works similarly to a dictionary, so it can be
updated with new values.

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
will use the setting defined in the last import.  This enables robust
configuration setups.  :meth:`~flask.Config.from_envvar` can help achieve this.

.. sourcecode:: python

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

Lastly, you will add a method that allows for easy connections to the
specified database.  This can be used to open a connection on request and
also from the interactive Python shell or a script.  This will come in
handy later.  You can create a simple database connection through SQLite and
then tell it to use the :class:`sqlite3.Row` object to represent rows.
This allows the rows to be treated as if they were dictionaries instead of
tuples.

.. sourcecode:: python

    def connect_db():
        """Connects to the specific database."""
        rv = sqlite3.connect(app.config['DATABASE'])
        rv.row_factory = sqlite3.Row
        return rv

In the next section you will see how to run the application.

Continue with :ref:`tutorial-setuptools`.
