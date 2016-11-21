.. _extension-dev:

Flask Extension Development
===========================

Flask, being a microframework, often requires some repetitive steps to get
a third party library working.  Because very often these steps could be
abstracted to support multiple projects the `Flask Extension Registry`_
was created.

If you want to create your own Flask extension for something that does not
exist yet, this guide to extension development will help you get your
extension running in no time and to feel like users would expect your
extension to behave.

.. _Flask Extension Registry: http://flask.pocoo.org/extensions/

Anatomy of an Extension
-----------------------

Extensions are all located in a package called ``flask_something``
where "something" is the name of the library you want to bridge.  So for
example if you plan to add support for a library named `simplexml` to
Flask, you would name your extension's package ``flask_simplexml``.

The name of the actual extension (the human readable name) however would
be something like "Flask-SimpleXML".  Make sure to include the name
"Flask" somewhere in that name and that you check the capitalization.
This is how users can then register dependencies to your extension in
their :file:`setup.py` files.

Flask sets up a redirect package called :data:`flask.ext` where users
should import the extensions from.  If you for instance have a package
called ``flask_something`` users would import it as
``flask.ext.something``.  This is done to transition from the old
namespace packages.  See :ref:`ext-import-transition` for more details.

But what do extensions look like themselves?  An extension has to ensure
that it works with multiple Flask application instances at once.  This is
a requirement because many people will use patterns like the
:ref:`app-factories` pattern to create their application as needed to aid
unittests and to support multiple configurations.  Because of that it is
crucial that your application supports that kind of behavior.

Most importantly the extension must be shipped with a :file:`setup.py` file and
registered on PyPI.  Also the development checkout link should work so
that people can easily install the development version into their
virtualenv without having to download the library by hand.

Flask extensions must be licensed under a BSD, MIT or more liberal license
to be able to be enlisted in the Flask Extension Registry.  Keep in mind
that the Flask Extension Registry is a moderated place and libraries will
be reviewed upfront if they behave as required.

"Hello Flaskext!"
-----------------

So let's get started with creating such a Flask extension.  The extension
we want to create here will provide very basic support for SQLite3.

First we create the following folder structure::

    flask-sqlite3/
        flask_sqlite3.py
        LICENSE
        README

Here's the contents of the most important files:

setup.py
````````

The next file that is absolutely required is the :file:`setup.py` file which is
used to install your Flask extension.  The following contents are
something you can work with::

    """
    Flask-SQLite3
    -------------

    This is the description for that library
    """
    from setuptools import setup


    setup(
        name='Flask-SQLite3',
        version='1.0',
        url='http://example.com/flask-sqlite3/',
        license='BSD',
        author='Your Name',
        author_email='your-email@example.com',
        description='Very short description',
        long_description=__doc__,
        py_modules=['flask_sqlite3'],
        # if you would be using a package instead use packages instead
        # of py_modules:
        # packages=['flask_sqlite3'],
        zip_safe=False,
        include_package_data=True,
        platforms='any',
        install_requires=[
            'Flask'
        ],
        classifiers=[
            'Environment :: Web Environment',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: BSD License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
            'Topic :: Software Development :: Libraries :: Python Modules'
        ]
    )

That's a lot of code but you can really just copy/paste that from existing
extensions and adapt.

flask_sqlite3.py
````````````````

Now this is where your extension code goes.  But how exactly should such
an extension look like?  What are the best practices?  Continue reading
for some insight.

Initializing Extensions
-----------------------

Many extensions will need some kind of initialization step.  For example,
consider an application that's currently connecting to SQLite like the
documentation suggests (:ref:`sqlite3`).  So how does the extension
know the name of the application object?

Quite simple: you pass it to it.

There are two recommended ways for an extension to initialize:

initialization functions:

    If your extension is called `helloworld` you might have a function
    called ``init_helloworld(app[, extra_args])`` that initializes the
    extension for that application.  It could attach before / after
    handlers etc.

classes:

    Classes work mostly like initialization functions but can later be
    used to further change the behavior.  For an example look at how the
    `OAuth extension`_ works: there is an `OAuth` object that provides
    some helper functions like `OAuth.remote_app` to create a reference to
    a remote application that uses OAuth.

What to use depends on what you have in mind.  For the SQLite 3 extension
we will use the class-based approach because it will provide users with an
object that handles opening and closing database connections.

What's important about classes is that they encourage to be shared around
on module level.  In that case, the object itself must not under any
circumstances store any application specific state and must be shareable
between different application.

The Extension Code
------------------

Here's the contents of the `flask_sqlite3.py` for copy/paste::

    import sqlite3
    from flask import current_app

    # Find the stack on which we want to store the database connection.
    # Starting with Flask 0.9, the _app_ctx_stack is the correct one,
    # before that we need to use the _request_ctx_stack.
    try:
        from flask import _app_ctx_stack as stack
    except ImportError:
        from flask import _request_ctx_stack as stack


    class SQLite3(object):

        def __init__(self, app=None):
            self.app = app
            if app is not None:
                self.init_app(app)

        def init_app(self, app):
            app.config.setdefault('SQLITE3_DATABASE', ':memory:')
            # Use the newstyle teardown_appcontext if it's available,
            # otherwise fall back to the request context
            if hasattr(app, 'teardown_appcontext'):
                app.teardown_appcontext(self.teardown)
            else:
                app.teardown_request(self.teardown)

        def connect(self):
            return sqlite3.connect(current_app.config['SQLITE3_DATABASE'])

        def teardown(self, exception):
            ctx = stack.top
            if hasattr(ctx, 'sqlite3_db'):
                ctx.sqlite3_db.close()

        @property
        def connection(self):
            ctx = stack.top
            if ctx is not None:
                if not hasattr(ctx, 'sqlite3_db'):
                    ctx.sqlite3_db = self.connect()
                return ctx.sqlite3_db


So here's what these lines of code do:

1.  The ``__init__`` method takes an optional app object and, if supplied, will
    call ``init_app``.
2.  The ``init_app`` method exists so that the ``SQLite3`` object can be
    instantiated without requiring an app object.  This method supports the
    factory pattern for creating applications.  The ``init_app`` will set the
    configuration for the database, defaulting to an in memory database if
    no configuration is supplied.  In addition, the ``init_app`` method attaches
    the ``teardown`` handler.  It will try to use the newstyle app context
    handler and if it does not exist, falls back to the request context
    one.
3.  Next, we define a ``connect`` method that opens a database connection.
4.  Finally, we add a ``connection`` property that on first access opens
    the database connection and stores it on the context.  This is also
    the recommended way to handling resources: fetch resources lazily the
    first time they are used.

    Note here that we're attaching our database connection to the top
    application context via ``_app_ctx_stack.top``. Extensions should use
    the top context for storing their own information with a sufficiently
    complex name.  Note that we're falling back to the
    ``_request_ctx_stack.top`` if the application is using an older
    version of Flask that does not support it.

So why did we decide on a class-based approach here?  Because using our
extension looks something like this::

    from flask import Flask
    from flask_sqlite3 import SQLite3

    app = Flask(__name__)
    app.config.from_pyfile('the-config.cfg')
    db = SQLite3(app)

You can then use the database from views like this::

    @app.route('/')
    def show_all():
        cur = db.connection.cursor()
        cur.execute(...)

Likewise if you are outside of a request but you are using Flask 0.9 or
later with the app context support, you can use the database in the same
way::

    with app.app_context():
        cur = db.connection.cursor()
        cur.execute(...)

At the end of the ``with`` block the teardown handles will be executed
automatically.

Additionally, the ``init_app`` method is used to support the factory pattern
for creating apps::

    db = Sqlite3()
    # Then later on.
    app = create_app('the-config.cfg')
    db.init_app(app)

Keep in mind that supporting this factory pattern for creating apps is required
for approved flask extensions (described below).

.. admonition:: Note on ``init_app``

   As you noticed, ``init_app`` does not assign ``app`` to ``self``.  This
   is intentional!  Class based Flask extensions must only store the
   application on the object when the application was passed to the
   constructor.  This tells the extension: I am not interested in using
   multiple applications.

   When the extension needs to find the current application and it does
   not have a reference to it, it must either use the
   :data:`~flask.current_app` context local or change the API in a way
   that you can pass the application explicitly.


Using _app_ctx_stack
--------------------

In the example above, before every request, a ``sqlite3_db`` variable is
assigned to ``_app_ctx_stack.top``.  In a view function, this variable is
accessible using the ``connection`` property of ``SQLite3``.  During the
teardown of a request, the ``sqlite3_db`` connection is closed.  By using
this pattern, the *same* connection to the sqlite3 database is accessible
to anything that needs it for the duration of the request.

If the :data:`~flask._app_ctx_stack` does not exist because the user uses
an old version of Flask, it is recommended to fall back to
:data:`~flask._request_ctx_stack` which is bound to a request.

Teardown Behavior
-----------------

*This is only relevant if you want to support Flask 0.6 and older*

Due to the change in Flask 0.7 regarding functions that are run at the end
of the request your extension will have to be extra careful there if it
wants to continue to support older versions of Flask.  The following
pattern is a good way to support both::

    def close_connection(response):
        ctx = _request_ctx_stack.top
        ctx.sqlite3_db.close()
        return response

    if hasattr(app, 'teardown_request'):
        app.teardown_request(close_connection)
    else:
        app.after_request(close_connection)

Strictly speaking the above code is wrong, because teardown functions are
passed the exception and typically don't return anything.  However because
the return value is discarded this will just work assuming that the code
in between does not touch the passed parameter.

Learn from Others
-----------------

This documentation only touches the bare minimum for extension
development.  If you want to learn more, it's a very good idea to check
out existing extensions on the `Flask Extension Registry`_.  If you feel
lost there is still the `mailinglist`_ and the `IRC channel`_ to get some
ideas for nice looking APIs.  Especially if you do something nobody before
you did, it might be a very good idea to get some more input.  This not
only to get an idea about what people might want to have from an
extension, but also to avoid having multiple developers working on pretty
much the same side by side.

Remember: good API design is hard, so introduce your project on the
mailinglist, and let other developers give you a helping hand with
designing the API.

The best Flask extensions are extensions that share common idioms for the
API.  And this can only work if collaboration happens early.

Approved Extensions
-------------------

Flask also has the concept of approved extensions.  Approved extensions
are tested as part of Flask itself to ensure extensions do not break on
new releases.  These approved extensions are listed on the `Flask
Extension Registry`_ and marked appropriately.  If you want your own
extension to be approved you have to follow these guidelines:

0.  An approved Flask extension requires a maintainer. In the event an
    extension author would like to move beyond the project, the project should
    find a new maintainer including full source hosting transition and PyPI
    access.  If no maintainer is available, give access to the Flask core team.
1.  An approved Flask extension must provide exactly one package or module
    named ``flask_extensionname``.
2.  It must ship a testing suite that can either be invoked with ``make test``
    or ``python setup.py test``.  For test suites invoked with ``make
    test`` the extension has to ensure that all dependencies for the test
    are installed automatically.  If tests are invoked with ``python setup.py
    test``, test dependencies can be specified in the :file:`setup.py` file.  The
    test suite also has to be part of the distribution.
3.  APIs of approved extensions will be checked for the following
    characteristics:

    -   an approved extension has to support multiple applications
        running in the same Python process.
    -   it must be possible to use the factory pattern for creating
        applications.

4.  The license must be BSD/MIT/WTFPL licensed.
5.  The naming scheme for official extensions is *Flask-ExtensionName* or
    *ExtensionName-Flask*.
6.  Approved extensions must define all their dependencies in the
    :file:`setup.py` file unless a dependency cannot be met because it is not
    available on PyPI.
7.  The extension must have documentation that uses one of the two Flask
    themes for Sphinx documentation.
8.  The setup.py description (and thus the PyPI description) has to
    link to the documentation, website (if there is one) and there
    must be a link to automatically install the development version
    (``PackageName==dev``).
9.  The ``zip_safe`` flag in the setup script must be set to ``False``,
    even if the extension would be safe for zipping.
10. An extension currently has to support Python 2.6 as well as
    Python 2.7


.. _ext-import-transition:

Extension Import Transition
---------------------------

In early versions of Flask we recommended using namespace packages for Flask
extensions, of the form ``flaskext.foo``. This turned out to be problematic in
practice because it meant that multiple ``flaskext`` packages coexist.
Consequently we have recommended to name extensions ``flask_foo`` over
``flaskext.foo`` for a long time.

Flask 0.8 introduced a redirect import system as a compatibility aid for app
developers: Importing ``flask.ext.foo`` would try ``flask_foo`` and
``flaskext.foo`` in that order.

As of Flask 0.11, most Flask extensions have transitioned to the new naming
schema. The ``flask.ext.foo`` compatibility alias is still in Flask 0.11 but is
now deprecated -- you should use ``flask_foo``.


.. _OAuth extension: http://pythonhosted.org/Flask-OAuth/
.. _mailinglist: http://flask.pocoo.org/mailinglist/
.. _IRC channel: http://flask.pocoo.org/community/irc/
