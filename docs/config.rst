Configuration Handling
======================

Applications need some kind of configuration.  There are different settings
you might want to change depending on the application environment like
toggling the debug mode, setting the secret key, and other such
environment-specific things.

The way Flask is designed usually requires the configuration to be
available when the application starts up.  You can hard code the
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
    app.config['TESTING'] = True

Certain configuration values are also forwarded to the
:attr:`~flask.Flask` object so you can read and write them from there::

    app.testing = True

To update multiple keys at once you can use the :meth:`dict.update`
method::

    app.config.update(
        TESTING=True,
        SECRET_KEY=b'_5#y2L"F4Q8z\n\xec]/'
    )


Environment and Debug Features
------------------------------

The :data:`ENV` and :data:`DEBUG` config values are special because they
may behave inconsistently if changed after the app has begun setting up.
In order to set the environment and debug mode reliably, Flask uses
environment variables.

The environment is used to indicate to Flask, extensions, and other
programs, like Sentry, what context Flask is running in. It is
controlled with the :envvar:`FLASK_ENV` environment variable and
defaults to ``production``.

Setting :envvar:`FLASK_ENV` to ``development`` will enable debug mode.
``flask run`` will use the interactive debugger and reloader by default
in debug mode. To control this separately from the environment, use the
:envvar:`FLASK_DEBUG` flag.

.. versionchanged:: 1.0
    Added :envvar:`FLASK_ENV` to control the environment separately
    from debug mode. The development environment enables debug mode.

To switch Flask to the development environment and enable debug mode,
set :envvar:`FLASK_ENV`::

    $ export FLASK_ENV=development
    $ flask run

(On Windows, use ``set`` instead of ``export``.)

Using the environment variables as described above is recommended. While
it is possible to set :data:`ENV` and :data:`DEBUG` in your config or
code, this is strongly discouraged. They can't be read early by the
``flask`` command, and some systems or extensions may have already
configured themselves based on a previous value.


Builtin Configuration Values
----------------------------

The following configuration values are used internally by Flask:

.. py:data:: ENV

    What environment the app is running in. Flask and extensions may
    enable behaviors based on the environment, such as enabling debug
    mode. The :attr:`~flask.Flask.env` attribute maps to this config
    key. This is set by the :envvar:`FLASK_ENV` environment variable and
    may not behave as expected if set in code.

    **Do not enable development when deploying in production.**

    Default: ``'production'``

    .. versionadded:: 1.0

.. py:data:: DEBUG

    Whether debug mode is enabled. When using ``flask run`` to start the
    development server, an interactive debugger will be shown for
    unhandled exceptions, and the server will be reloaded when code
    changes. The :attr:`~flask.Flask.debug` attribute maps to this
    config key. This is enabled when :data:`ENV` is ``'development'``
    and is overridden by the ``FLASK_DEBUG`` environment variable. It
    may not behave as expected if set in code.

    **Do not enable debug mode when deploying in production.**

    Default: ``True`` if :data:`ENV` is ``'development'``, or ``False``
    otherwise.

.. py:data:: TESTING

    Enable testing mode. Exceptions are propagated rather than handled by the
    the app's error handlers. Extensions may also change their behavior to
    facilitate easier testing. You should enable this in your own tests.

    Default: ``False``

.. py:data:: PROPAGATE_EXCEPTIONS

    Exceptions are re-raised rather than being handled by the app's error
    handlers. If not set, this is implicitly true if ``TESTING`` or ``DEBUG``
    is enabled.

    Default: ``None``

.. py:data:: PRESERVE_CONTEXT_ON_EXCEPTION

    Don't pop the request context when an exception occurs. If not set, this
    is true if ``DEBUG`` is true. This allows debuggers to introspect the
    request data on errors, and should normally not need to be set directly.

    Default: ``None``

.. py:data:: TRAP_HTTP_EXCEPTIONS

    If there is no handler for an ``HTTPException``-type exception, re-raise it
    to be handled by the interactive debugger instead of returning it as a
    simple error response.

    Default: ``False``

.. py:data:: TRAP_BAD_REQUEST_ERRORS

    Trying to access a key that doesn't exist from request dicts like ``args``
    and ``form`` will return a 400 Bad Request error page. Enable this to treat
    the error as an unhandled exception instead so that you get the interactive
    debugger. This is a more specific version of ``TRAP_HTTP_EXCEPTIONS``. If
    unset, it is enabled in debug mode.

    Default: ``None``

.. py:data:: SECRET_KEY

    A secret key that will be used for securely signing the session cookie
    and can be used for any other security related needs by extensions or your
    application. It should be a long random ``bytes`` or ``str``. For
    example, copy the output of this to your config::

        $ python -c 'import os; print(os.urandom(16))'
        b'_5#y2L"F4Q8z\n\xec]/'

    **Do not reveal the secret key when posting questions or committing code.**

    Default: ``None``

.. py:data:: SESSION_COOKIE_NAME

    The name of the session cookie. Can be changed in case you already have a
    cookie with the same name.

    Default: ``'session'``

.. py:data:: SESSION_COOKIE_DOMAIN

    The domain match rule that the session cookie will be valid for. If not
    set, the cookie will be valid for all subdomains of :data:`SERVER_NAME`.
    If ``False``, the cookie's domain will not be set.

    Default: ``None``

.. py:data:: SESSION_COOKIE_PATH

    The path that the session cookie will be valid for. If not set, the cookie
    will be valid underneath ``APPLICATION_ROOT`` or ``/`` if that is not set.

    Default: ``None``

.. py:data:: SESSION_COOKIE_HTTPONLY

    Browsers will not allow JavaScript access to cookies marked as "HTTP only"
    for security.

    Default: ``True``

.. py:data:: SESSION_COOKIE_SECURE

    Browsers will only send cookies with requests over HTTPS if the cookie is
    marked "secure". The application must be served over HTTPS for this to make
    sense.

    Default: ``False``

.. py:data:: SESSION_COOKIE_SAMESITE

    Restrict how cookies are sent with requests from external sites. Can
    be set to ``'Lax'`` (recommended) or ``'Strict'``.
    See :ref:`security-cookie`.

    Default: ``None``

    .. versionadded:: 1.0

.. py:data:: PERMANENT_SESSION_LIFETIME

    If ``session.permanent`` is true, the cookie's expiration will be set this
    number of seconds in the future. Can either be a
    :class:`datetime.timedelta` or an ``int``.

    Flask's default cookie implementation validates that the cryptographic
    signature is not older than this value.

    Default: ``timedelta(days=31)`` (``2678400`` seconds)

.. py:data:: SESSION_REFRESH_EACH_REQUEST

    Control whether the cookie is sent with every response when
    ``session.permanent`` is true. Sending the cookie every time (the default)
    can more reliably keep the session from expiring, but uses more bandwidth.
    Non-permanent sessions are not affected.

    Default: ``True``

.. py:data:: USE_X_SENDFILE

    When serving files, set the ``X-Sendfile`` header instead of serving the
    data with Flask. Some web servers, such as Apache, recognize this and serve
    the data more efficiently. This only makes sense when using such a server.

    Default: ``False``

.. py:data:: SEND_FILE_MAX_AGE_DEFAULT

    When serving files, set the cache control max age to this number of
    seconds.  Can either be a :class:`datetime.timedelta` or an ``int``.
    Override this value on a per-file basis using
    :meth:`~flask.Flask.get_send_file_max_age` on the application or blueprint.

    Default: ``timedelta(hours=12)`` (``43200`` seconds)

.. py:data:: SERVER_NAME

    Inform the application what host and port it is bound to. Required
    for subdomain route matching support.

    If set, will be used for the session cookie domain if
    :data:`SESSION_COOKIE_DOMAIN` is not set. Modern web browsers will
    not allow setting cookies for domains without a dot. To use a domain
    locally, add any names that should route to the app to your
    ``hosts`` file. ::

        127.0.0.1 localhost.dev

    If set, ``url_for`` can generate external URLs with only an application
    context instead of a request context.

    Default: ``None``

.. py:data:: APPLICATION_ROOT

    Inform the application what path it is mounted under by the application /
    web server.  This is used for generating URLs outside the context of a
    request (inside a request, the dispatcher is responsible for setting
    ``SCRIPT_NAME`` instead; see :doc:`/patterns/appdispatch`
    for examples of dispatch configuration).

    Will be used for the session cookie path if ``SESSION_COOKIE_PATH`` is not
    set.

    Default: ``'/'``

.. py:data:: PREFERRED_URL_SCHEME

    Use this scheme for generating external URLs when not in a request context.

    Default: ``'http'``

.. py:data:: MAX_CONTENT_LENGTH

    Don't read more than this many bytes from the incoming request data. If not
    set and the request does not specify a ``CONTENT_LENGTH``, no data will be
    read for security.

    Default: ``None``

.. py:data:: JSON_AS_ASCII

    Serialize objects to ASCII-encoded JSON. If this is disabled, the
    JSON returned from ``jsonify`` will contain Unicode characters. This
    has security implications when rendering the JSON into JavaScript in
    templates, and should typically remain enabled.

    Default: ``True``

.. py:data:: JSON_SORT_KEYS

    Sort the keys of JSON objects alphabetically. This is useful for caching
    because it ensures the data is serialized the same way no matter what
    Python's hash seed is. While not recommended, you can disable this for a
    possible performance improvement at the cost of caching.

    Default: ``True``

.. py:data:: JSONIFY_PRETTYPRINT_REGULAR

    ``jsonify`` responses will be output with newlines, spaces, and indentation
    for easier reading by humans. Always enabled in debug mode.

    Default: ``False``

.. py:data:: JSONIFY_MIMETYPE

    The mimetype of ``jsonify`` responses.

    Default: ``'application/json'``

.. py:data:: TEMPLATES_AUTO_RELOAD

    Reload templates when they are changed. If not set, it will be enabled in
    debug mode.

    Default: ``None``

.. py:data:: EXPLAIN_TEMPLATE_LOADING

    Log debugging information tracing how a template file was loaded. This can
    be useful to figure out why a template was not loaded or the wrong file
    appears to be loaded.

    Default: ``False``

.. py:data:: MAX_COOKIE_SIZE

    Warn if cookie headers are larger than this many bytes. Defaults to
    ``4093``. Larger cookies may be silently ignored by browsers. Set to
    ``0`` to disable the warning.

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

.. versionchanged:: 1.0
    ``LOGGER_NAME`` and ``LOGGER_HANDLER_POLICY`` were removed. See
    :doc:`/logging` for information about configuration.

    Added :data:`ENV` to reflect the :envvar:`FLASK_ENV` environment
    variable.

    Added :data:`SESSION_COOKIE_SAMESITE` to control the session
    cookie's ``SameSite`` option.

    Added :data:`MAX_COOKIE_SIZE` to control a warning from Werkzeug.


Configuring from Python Files
-----------------------------

Configuration becomes more useful if you can store it in a separate file,
ideally located outside the actual application package. This makes
packaging and distributing your application possible via various package
handling tools (:doc:`/patterns/distribute`) and finally modifying the
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

    > set YOURAPPLICATION_SETTINGS=\path\to\settings.cfg

The configuration files themselves are actual Python files.  Only values
in uppercase are actually stored in the config object later on.  So make
sure to use uppercase letters for your config keys.

Here is an example of a configuration file::

    # Example configuration
    SECRET_KEY = b'_5#y2L"F4Q8z\n\xec]/'

Make sure to load the configuration very early on, so that extensions have
the ability to access the configuration when starting up.  There are other
methods on the config object as well to load from individual files.  For a
complete reference, read the :class:`~flask.Config` object's
documentation.


Configuring from Data Files
---------------------------

It is also possible to load configuration from a file in a format of
your choice using :meth:`~flask.Config.from_file`. For example to load
from a TOML file:

.. code-block:: python

    import toml
    app.config.from_file("config.toml", load=toml.load)

Or from a JSON file:

.. code-block:: python

    import json
    app.config.from_file("config.json", load=json.load)


Configuring from Environment Variables
--------------------------------------

In addition to pointing to configuration files using environment variables, you
may find it useful (or necessary) to control your configuration values directly
from the environment.

Environment variables can be set on Linux or OS X with the export command in
the shell before starting the server::

    $ export SECRET_KEY='5f352379324c22463451387a0aec5d2f'
    $ export MAIL_ENABLED=false
    $ python run-app.py
     * Running on http://127.0.0.1:5000/

On Windows systems use the ``set`` builtin instead::

    > set SECRET_KEY='5f352379324c22463451387a0aec5d2f'

While this approach is straightforward to use, it is important to remember that
environment variables are strings -- they are not automatically deserialized
into Python types.

Here is an example of a configuration file that uses environment variables::

    import os

    _mail_enabled = os.environ.get("MAIL_ENABLED", default="true")
    MAIL_ENABLED = _mail_enabled.lower() in {"1", "t", "true"}

    SECRET_KEY = os.environ.get("SECRET_KEY")

    if not SECRET_KEY:
        raise ValueError("No SECRET_KEY set for Flask application")


Notice that any value besides an empty string will be interpreted as a boolean
``True`` value in Python, which requires care if an environment explicitly sets
values intended to be ``False``.

Make sure to load the configuration very early on, so that extensions have the
ability to access the configuration when starting up.  There are other methods
on the config object as well to load from individual files.  For a complete
reference, read the :class:`~flask.Config` class documentation.


Configuration Best Practices
----------------------------

The downside with the approach mentioned earlier is that it makes testing
a little harder.  There is no single 100% solution for this problem in
general, but there are a couple of things you can keep in mind to improve
that experience:

1.  Create your application in a function and register blueprints on it.
    That way you can create multiple instances of your application with
    different configurations attached which makes unit testing a lot
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
and import different hard-coded files based on that.

An interesting pattern is also to use classes and inheritance for
configuration::

    class Config(object):
        TESTING = False

    class ProductionConfig(Config):
        DATABASE_URI = 'mysql://user@localhost/foo'

    class DevelopmentConfig(Config):
        DATABASE_URI = "sqlite:////tmp/foo.db"

    class TestingConfig(Config):
        DATABASE_URI = 'sqlite:///:memory:'
        TESTING = True

To enable such a config you just have to call into
:meth:`~flask.Config.from_object`::

    app.config.from_object('configmodule.ProductionConfig')

Note that :meth:`~flask.Config.from_object` does not instantiate the class
object. If you need to instantiate the class, such as to access a property,
then you must do so before calling :meth:`~flask.Config.from_object`::

    from configmodule import ProductionConfig
    app.config.from_object(ProductionConfig())

    # Alternatively, import via string:
    from werkzeug.utils import import_string
    cfg = import_string('configmodule.ProductionConfig')()
    app.config.from_object(cfg)

Instantiating the configuration object allows you to use ``@property`` in
your configuration classes::

    class Config(object):
        """Base config, uses staging database server."""
        TESTING = False
        DB_SERVER = '192.168.1.56'

        @property
        def DATABASE_URI(self):  # Note: all caps
            return f"mysql://user@{self.DB_SERVER}/foo"

    class ProductionConfig(Config):
        """Uses production database server."""
        DB_SERVER = '192.168.19.32'

    class DevelopmentConfig(Config):
        DB_SERVER = 'localhost'

    class TestingConfig(Config):
        DB_SERVER = 'localhost'
        DATABASE_URI = 'sqlite:///:memory:'

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
    :doc:`/patterns/fabric` pattern.

.. _fabric: https://www.fabfile.org/


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

        $PREFIX/lib/pythonX.Y/site-packages/myapp
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
from a module and then override the config from a file in the instance
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
