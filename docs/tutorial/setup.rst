.. _tutorial-setup:

Step 2: Application Setup Code
==============================

Now that we have the schema in place we can create the application module.
Let's call it `flaskr.py` inside the `flaskr` folder.  For starters we
will add the imports we will need as well as the config section.  For
small applications it's a possibility to drop the configuration directly
into the module which we will be doing here.  However a cleaner solution
would be to create a separate `.ini` or `.py` file and load that or import
the values from there.

In `flaskr.py`::

    # all the imports
    import sqlite3
    from flask import Flask, request, session, g, redirect, url_for, \
         abort, render_template, flash

    # configuration
    DATABASE = '/tmp/flaskr.db'
    DEBUG = True
    SECRET_KEY = 'development key'
    USERNAME = 'admin'
    PASSWORD = 'default'

Next we can create our actual application and initialize it with the
config from the same file, in `flaskr.py`::

    # create our little application :)
    app = Flask(__name__)
    app.config.from_object(__name__)

:meth:`~flask.Config.from_object` will look at the given object (if it's a
string it will import it) and then look for all uppercase variables
defined there.  In our case, the configuration we just wrote a few lines
of code above.  You can also move that into a separate file.

Usually, it is a good idea to load a configuration from a configurable
file. This is what :meth:`~flask.Config.from_envvar` can do, replacing the
:meth:`~flask.Config.from_object` line above::

    app.config.from_envvar('FLASKR_SETTINGS', silent=True)

That way someone can set an environment variable called
:envvar:`FLASKR_SETTINGS` to specify a config file to be loaded which will then
override the default values. The silent switch just tells Flask to not complain
if no such environment key is set.

The `secret_key` is needed to keep the client-side sessions secure.
Choose that key wisely and as hard to guess and complex as possible.  The
debug flag enables or disables the interactive debugger.  *Never leave
debug mode activated in a production system*, because it will allow users to
execute code on the server!

We also add a method to easily connect to the database specified.  That
can be used to open a connection on request and also from the interactive
Python shell or a script.  This will come in handy later.

::

    def connect_db():
        return sqlite3.connect(app.config['DATABASE'])

Finally we just add a line to the bottom of the file that fires up the
server if we want to run that file as a standalone application::

    if __name__ == '__main__':
        app.run()

With that out of the way you should be able to start up the application
without problems.  Do this with the following command::

   python flaskr.py

You will see a message telling you that server has started along with
the address at which you can access it.

When you head over to the server in your browser you will get an 404
page not found error because we don't have any views yet.  But we will
focus on that a little later.  First we should get the database working.

.. admonition:: Externally Visible Server

   Want your server to be publicly available?  Check out the
   :ref:`externally visible server <public-server>` section for more
   information.

Continue with :ref:`tutorial-dbinit`.
