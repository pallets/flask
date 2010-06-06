.. _config:

Configuration Handling
======================

.. versionadded:: 0.3

Applications need some kind of configuration.  There are different things
you might want to change.  Like toggling debug mode, the secret key and a
lot of very similar things.

The way Flask is designed usually requires the configuration to be
available when the application starts up.  You can either hardcode the
configuration in the code which for many small applications is not
actually that bad, but there are better ways.

Independent of how you load your config, there is a config object
available which holds the loaded configuration values:
The :attr:`~flask.Flask.config` attribute of the :class:`~flask.Flask`
object.  This is the place where Flask itself puts certain configuration
values and also where extensions can put their configuration values.  But
this is also where you can have your own configuration.

Configuration Basics
--------------------

The :attr:`~flask.Flask.config` is actually a subclass of a dictionary and
can be modified just like any dictionary::

    app = Flask(__name__)
    app.config['DEBUG'] = True

Certain configuration values are also forwarded to the
:attr:`~flask.Flask` object so that you can read and write them from
there::

    app.debug = True

To update multiple keys at once you can use the :meth:`dict.update`
method::

    app.config.update(
        DEBUG=True,
        SECRET_KEY='...'
    )

Builtin Configuration Values
----------------------------

The following configuration values are used internally by Flask:

.. tabularcolumns:: |p{6.5cm}|p{8.5cm}|

=============================== =========================================
``DEBUG``                       enable/disable debug mode
``TESTING``                     enable/disable testing mode
``SECRET_KEY``                  the secret key
``SESSION_COOKIE_NAME``         the name of the session cookie
``PERMANENT_SESSION_LIFETIME``  the lifetime of a permanent session as
                                :class:`datetime.timedelta` object.
``USE_X_SENDFILE``              enable/disable x-sendfile
=============================== =========================================

Configuring from Files
----------------------

Configuration becomes more useful if you can configure from a file.  And
ideally that file would be outside of the actual application package that
you can install the package with distribute (:ref:`distribute-deployment`)
and still modify that file afterwards.

So a common pattern is this::

    app = Flask(__name__)
    app.config.from_object('yourapplication.default_settings')
    app.config.from_envvar('YOURAPPLICATION_SETTINGS')

What this does is first loading the configuration from the
`yourapplication.default_settings` module and then overrides the values
with the contents of the file the :envvar:`YOURAPPLICATION_SETTINGS`
environment variable points to.  This environment variable can be set on
Linux or OS X with the export command in the shell before starting the
server::

    $ export YOURAPPLICATION_SETTINGS=/path/to/settings.cfg
    $ python run-app.py
     * Running on http://127.0.0.1:5000/
     * Restarting with reloader...

On Windows systems use the `set` builtin instead::

    >set YOURAPPLICATION_SETTINGS=\path\to\settings.cfg

The configuration files themselves are actual Python files.  Only values
in uppercase are actually stored in the config object later on.  So make
sure to use uppercase letters for your config keys.

Here an example configuration file::

    DEBUG = False
    SECRET_KEY = '?\xbf,\xb4\x8d\xa3"<\x9c\xb0@\x0f5\xab,w\xee\x8d$0\x13\x8b83'

Make sure to load the configuration very early on so that extensions have
the ability to access the configuration when starting up.  There are other
methods on the config object as well to load from individual files.  For a
complete reference, read the :class:`~flask.Config` object's
documentation.


Configuration Best Practices
----------------------------

The downside with the approach mentioned earlier is that it makes testing
a little harder.  There is no one 100% solution for this problem in
general, but there are a couple of things you can do to improve that
experience:

1.  create your application in a function and register modules on it.
    That way you can create multiple instances of your application with
    different configurations attached which makes unittesting a lot
    easier.  You can use this to pass in configuration as needed.

2.  Do not write code that needs the configuration at import time.  If you
    limit yourself to request-only accesses to the configuration you can
    reconfigure the object later on as needed.
