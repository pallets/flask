.. _config:

Configuration Handling
======================

.. versionadded:: 0.3

Applications need some kind of configuration.  There are different settings
you might want to change depending on the application environment like
toggling the debug mode, setting the secret key, and other such
environment-specific things.

The way Flask is designed usually requires the configuration to be
available when the application starts up.  You can hardcode the
configuration in the code, which for many small applications is not
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
:attr:`~flask.Flask` object so you can read and write them from there::

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

================================= =========================================
``DEBUG``                         enable/disable debug mode
``TESTING``                       enable/disable testing mode
``PROPAGATE_EXCEPTIONS``          explicitly enable or disable the
                                  propagation of exceptions.  If not set or
                                  explicitly set to ``None`` this is
                                  implicitly true if either ``TESTING`` or
                                  ``DEBUG`` is true.
``PRESERVE_CONTEXT_ON_EXCEPTION`` By default if the application is in
                                  debug mode the request context is not
                                  popped on exceptions to enable debuggers
                                  to introspect the data.  This can be
                                  disabled by this key.  You can also use
                                  this setting to force-enable it for non
                                  debug execution which might be useful to
                                  debug production applications (but also
                                  very risky).
``SECRET_KEY``                    the secret key
``SESSION_COOKIE_NAME``           the name of the session cookie
``SESSION_COOKIE_DOMAIN``         the domain for the session cookie.  If
                                  this is not set, the cookie will be
                                  valid for all subdomains of
                                  ``SERVER_NAME``.
``SESSION_COOKIE_PATH``           the path for the session cookie.  If
                                  this is not set the cookie will be valid
                                  for all of ``APPLICATION_ROOT`` or if
                                  that is not set for ``'/'``.
``SESSION_COOKIE_HTTPONLY``       controls if the cookie should be set
                                  with the httponly flag.  Defaults to
                                  ``True``.
``SESSION_COOKIE_SECURE``         controls if the cookie should be set
                                  with the secure flag.  Defaults to
                                  ``False``.
``PERMANENT_SESSION_LIFETIME``    the lifetime of a permanent session as
                                  :class:`datetime.timedelta` object.
                                  Starting with Flask 0.8 this can also be
                                  an integer representing seconds.
``SESSION_REFRESH_EACH_REQUEST``  this flag controls how permanent
                                  sessions are refreshed.  If set to ``True``
                                  (which is the default) then the cookie
                                  is refreshed each request which
                                  automatically bumps the lifetime.  If
                                  set to ``False`` a `set-cookie` header is
                                  only sent if the session is modified.
                                  Non permanent sessions are not affected
                                  by this.
``USE_X_SENDFILE``                enable/disable x-sendfile
``LOGGER_NAME``                   the name of the logger
``LOGGER_HANDLER_POLICY``         the policy of the default logging
                                  handler.  The default is ``'always'``
                                  which means that the default logging
                                  handler is always active.  ``'debug'``
                                  will only activate logging in debug
                                  mode, ``'production'`` will only log in
                                  production and ``'never'`` disables it
                                  entirely.
``SERVER_NAME``                   the name and port number of the server.
                                  Required for subdomain support (e.g.:
                                  ``'myapp.dev:5000'``)  Note that
                                  localhost does not support subdomains so
                                  setting this to “localhost” does not
                                  help.  Setting a ``SERVER_NAME`` also
                                  by default enables URL generation
                                  without a request context but with an
                                  application context.
``APPLICATION_ROOT``              If the application does not occupy
                                  a whole domain or subdomain this can
                                  be set to the path where the application
                                  is configured to live.  This is for
                                  session cookie as path value.  If
                                  domains are used, this should be
                                  ``None``.
``MAX_CONTENT_LENGTH``            If set to a value in bytes, Flask will
                                  reject incoming requests with a
                                  content length greater than this by
                                  returning a 413 status code.
``SEND_FILE_MAX_AGE_DEFAULT``     Default cache control max age to use with
                                  :meth:`~flask.Flask.send_static_file` (the
                                  default static file handler) and
                                  :func:`~flask.send_file`, as
                                  :class:`datetime.timedelta` or as seconds.
                                  Override this value on a per-file
                                  basis using the
                                  :meth:`~flask.Flask.get_send_file_max_age`
                                  hook on :class:`~flask.Flask` or
                                  :class:`~flask.Blueprint`,
                                  respectively. Defaults to 43200 (12 hours).
``TRAP_HTTP_EXCEPTIONS``          If this is set to ``True`` Flask will
                                  not execute the error handlers of HTTP
                                  exceptions but instead treat the
                                  exception like any other and bubble it
                                  through the exception stack.  This is
                                  helpful for hairy debugging situations
                                  where you have to find out where an HTTP
                                  exception is coming from.
``TRAP_BAD_REQUEST_ERRORS``       Werkzeug's internal data structures that
                                  deal with request specific data will
                                  raise special key errors that are also
                                  bad request exceptions.  Likewise many
                                  operations can implicitly fail with a
                                  BadRequest exception for consistency.
                                  Since it's nice for debugging to know
                                  why exactly it failed this flag can be
                                  used to debug those situations.  If this
                                  config is set to ``True`` you will get
                                  a regular traceback instead.
``PREFERRED_URL_SCHEME``          The URL scheme that should be used for
                                  URL generation if no URL scheme is
                                  available.  This defaults to ``http``.
``JSON_AS_ASCII``                 By default Flask serialize object to
                                  ascii-encoded JSON.  If this is set to
                                  ``False`` Flask will not encode to ASCII
                                  and output strings as-is and return
                                  unicode strings.  ``jsonify`` will
                                  automatically encode it in ``utf-8``
                                  then for transport for instance.
``JSON_SORT_KEYS``                By default Flask will serialize JSON
                                  objects in a way that the keys are
                                  ordered.  This is done in order to
                                  ensure that independent of the hash seed
                                  of the dictionary the return value will
                                  be consistent to not trash external HTTP
                                  caches.  You can override the default
                                  behavior by changing this variable.
                                  This is not recommended but might give
                                  you a performance improvement on the
                                  cost of cacheability.
``JSONIFY_PRETTYPRINT_REGULAR``   If this is set to ``True`` (the default)
                                  jsonify responses will be pretty printed
                                  if they are not requested by an
                                  XMLHttpRequest object (controlled by
                                  the ``X-Requested-With`` header)
``JSONIFY_MIMETYPE``              MIME type used for jsonify responses.
``TEMPLATES_AUTO_RELOAD``         Whether to check for modifications of
                                  the template source and reload it
                                  automatically. By default the value is
                                  ``None`` which means that Flask checks
                                  original file only in debug mode.
``EXPLAIN_TEMPLATE_LOADING``      If this is enabled then every attempt to
                                  load a template will write an info
                                  message to the logger explaining the
                                  attempts to locate the template.  This
                                  can be useful to figure out why
                                  templates cannot be found or wrong
                                  templates appear to be loaded.
================================= =========================================

.. admonition:: More on ``SERVER_NAME``

   The ``SERVER_NAME`` key is used for the subdomain support.  Because
   Flask cannot guess the subdomain part without the knowledge of the
   actual server name, this is required if you want to work with
   subdomains.  This is also used for the session cookie.

   Please keep in mind that not only Flask has the problem of not knowing
   what subdomains are, your web browser does as well.  Most modern web
   browsers will not allow cross-subdomain cookies to be set on a
   server name without dots in it.  So if your server name is
   ``'localhost'`` you will not be able to set a cookie for
   ``'localhost'`` and every subdomain of it.  Please choose a different
   server name in that case, like ``'myapplication.local'`` and add
   this name + the subdomains you want to use into your host config
   or setup a local `bind`_.

.. _bind: https://www.isc.org/downloads/bind/

.. versionadded:: 0.4
   ``LOGGER_NAME``

.. versionadded:: 0.5
   ``SERVER_NAME``

.. versionadded:: 0.6
   ``MAX_CONTENT_LENGTH``

.. versionadded:: 0.7
   ``PROPAGATE_EXCEPTIONS``, ``PRESERVE_CONTEXT_ON_EXCEPTION``

.. versionadded:: 0.8
   ``TRAP_BAD_REQUEST_ERRORS``, ``TRAP_HTTP_EXCEPTIONS``,
   ``APPLICATION_ROOT``, ``SESSION_COOKIE_DOMAIN``,
   ``SESSION_COOKIE_PATH``, ``SESSION_COOKIE_HTTPONLY``,
   ``SESSION_COOKIE_SECURE``

.. versionadded:: 0.9
   ``PREFERRED_URL_SCHEME``

.. versionadded:: 0.10
   ``JSON_AS_ASCII``, ``JSON_SORT_KEYS``, ``JSONIFY_PRETTYPRINT_REGULAR``

.. versionadded:: 0.11
   ``SESSION_REFRESH_EACH_REQUEST``, ``TEMPLATES_AUTO_RELOAD``,
   ``LOGGER_HANDLER_POLICY``, ``EXPLAIN_TEMPLATE_LOADING``

Configuring from Files
----------------------

Configuration becomes more useful if you can store it in a separate file,
ideally located outside the actual application package. This makes
packaging and distributing your application possible via various package
handling tools (:ref:`distribute-deployment`) and finally modifying the
configuration file afterwards.

So a common pattern is this::

    app = Flask(__name__)
    app.config.from_object('yourapplication.default_settings')
    app.config.from_envvar('YOURAPPLICATION_SETTINGS')

This first loads the configuration from the
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

Here is an example of a configuration file::

    # Example configuration
    DEBUG = False
    SECRET_KEY = '?\xbf,\xb4\x8d\xa3"<\x9c\xb0@\x0f5\xab,w\xee\x8d$0\x13\x8b83'

Make sure to load the configuration very early on, so that extensions have
the ability to access the configuration when starting up.  There are other
methods on the config object as well to load from individual files.  For a
complete reference, read the :class:`~flask.Config` object's
documentation.


Configuration Best Practices
----------------------------

The downside with the approach mentioned earlier is that it makes testing
a little harder.  There is no single 100% solution for this problem in
general, but there are a couple of things you can keep in mind to improve
that experience:

1.  Create your application in a function and register blueprints on it.
    That way you can create multiple instances of your application with
    different configurations attached which makes unittesting a lot
    easier.  You can use this to pass in configuration as needed.

2.  Do not write code that needs the configuration at import time.  If you
    limit yourself to request-only accesses to the configuration you can
    reconfigure the object later on as needed.

.. _config-dev-prod:

Development / Production
------------------------

Most applications need more than one configuration.  There should be at
least separate configurations for the production server and the one used
during development.  The easiest way to handle this is to use a default
configuration that is always loaded and part of the version control, and a
separate configuration that overrides the values as necessary as mentioned
in the example above::

    app = Flask(__name__)
    app.config.from_object('yourapplication.default_settings')
    app.config.from_envvar('YOURAPPLICATION_SETTINGS')

Then you just have to add a separate :file:`config.py` file and export
``YOURAPPLICATION_SETTINGS=/path/to/config.py`` and you are done.  However
there are alternative ways as well.  For example you could use imports or
subclassing.

What is very popular in the Django world is to make the import explicit in
the config file by adding ``from yourapplication.default_settings
import *`` to the top of the file and then overriding the changes by hand.
You could also inspect an environment variable like
``YOURAPPLICATION_MODE`` and set that to `production`, `development` etc
and import different hardcoded files based on that.

An interesting pattern is also to use classes and inheritance for
configuration::

    class Config(object):
        DEBUG = False
        TESTING = False
        DATABASE_URI = 'sqlite://:memory:'

    class ProductionConfig(Config):
        DATABASE_URI = 'mysql://user@localhost/foo'

    class DevelopmentConfig(Config):
        DEBUG = True

    class TestingConfig(Config):
        TESTING = True

To enable such a config you just have to call into
:meth:`~flask.Config.from_object`::

    app.config.from_object('configmodule.ProductionConfig')

There are many different ways and it's up to you how you want to manage
your configuration files.  However here a list of good recommendations:

-   Keep a default configuration in version control.  Either populate the
    config with this default configuration or import it in your own
    configuration files before overriding values.
-   Use an environment variable to switch between the configurations.
    This can be done from outside the Python interpreter and makes
    development and deployment much easier because you can quickly and
    easily switch between different configs without having to touch the
    code at all.  If you are working often on different projects you can
    even create your own script for sourcing that activates a virtualenv
    and exports the development configuration for you.
-   Use a tool like `fabric`_ in production to push code and
    configurations separately to the production server(s).  For some
    details about how to do that, head over to the
    :ref:`fabric-deployment` pattern.

.. _fabric: http://www.fabfile.org/


.. _instance-folders:

Instance Folders
----------------

.. versionadded:: 0.8

Flask 0.8 introduces instance folders.  Flask for a long time made it
possible to refer to paths relative to the application's folder directly
(via :attr:`Flask.root_path`).  This was also how many developers loaded
configurations stored next to the application.  Unfortunately however this
only works well if applications are not packages in which case the root
path refers to the contents of the package.

With Flask 0.8 a new attribute was introduced:
:attr:`Flask.instance_path`.  It refers to a new concept called the
“instance folder”.  The instance folder is designed to not be under
version control and be deployment specific.  It's the perfect place to
drop things that either change at runtime or configuration files.

You can either explicitly provide the path of the instance folder when
creating the Flask application or you can let Flask autodetect the
instance folder.  For explicit configuration use the `instance_path`
parameter::

    app = Flask(__name__, instance_path='/path/to/instance/folder')

Please keep in mind that this path *must* be absolute when provided.

If the `instance_path` parameter is not provided the following default
locations are used:

-   Uninstalled module::

        /myapp.py
        /instance

-   Uninstalled package::

        /myapp
            /__init__.py
        /instance

-   Installed module or package::

        $PREFIX/lib/python2.X/site-packages/myapp
        $PREFIX/var/myapp-instance

    ``$PREFIX`` is the prefix of your Python installation.  This can be
    ``/usr`` or the path to your virtualenv.  You can print the value of
    ``sys.prefix`` to see what the prefix is set to.

Since the config object provided loading of configuration files from
relative filenames we made it possible to change the loading via filenames
to be relative to the instance path if wanted.  The behavior of relative
paths in config files can be flipped between “relative to the application
root” (the default) to “relative to instance folder” via the
`instance_relative_config` switch to the application constructor::

    app = Flask(__name__, instance_relative_config=True)

Here is a full example of how to configure Flask to preload the config
from a module and then override the config from a file in the config
folder if it exists::

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object('yourapplication.default_settings')
    app.config.from_pyfile('application.cfg', silent=True)

The path to the instance folder can be found via the
:attr:`Flask.instance_path`.  Flask also provides a shortcut to open a
file from the instance folder with :meth:`Flask.open_instance_resource`.

Example usage for both::

    filename = os.path.join(app.instance_path, 'application.cfg')
    with open(filename) as f:
        config = f.read()

    # or via open_instance_resource:
    with app.open_instance_resource('application.cfg') as f:
        config = f.read()
