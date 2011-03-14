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

Extensions are all located in a package called ``flaskext.something``
where "something" is the name of the library you want to bridge.  So for
example if you plan to add support for a library named `simplexml` to
Flask, you would name your extension's package ``flaskext.simplexml``.

The name of the actual extension (the human readable name) however would
be something like "Flask-SimpleXML".  Make sure to include the name
"Flask" somewhere in that name and that you check the capitalization.
This is how users can then register dependencies to your extension in
their `setup.py` files.

The magic that makes it possible to have your library in a package called
``flaskext.something`` is called a "namespace package".  Check out the
guide below how to create something like that.

But how do extensions look like themselves?  An extension has to ensure
that it works with multiple Flask application instances at once.  This is
a requirement because many people will use patterns like the
:ref:`app-factories` pattern to create their application as needed to aid
unittests and to support multiple configurations.  Because of that it is
crucial that your application supports that kind of behaviour.

Most importantly the extension must be shipped with a `setup.py` file and
registered on PyPI.  Also the development checkout link should work so
that people can easily install the development version into their
virtualenv without having to download the library by hand.

Flask extensions must be licensed as BSD or MIT or a more liberal license
to be enlisted on the Flask Extension Registry.  Keep in mind that the
Flask Extension Registry is a moderated place and libraries will be
reviewed upfront if they behave as required.

"Hello Flaskext!"
-----------------

So let's get started with creating such a Flask extension.  The extension
we want to create here will provide very basic support for SQLite3.

There is a script on github called `Flask Extension Wizard`_ which helps
you create the initial folder structure.  But for this very basic example
we want to create all by hand to get a better feeling for it.

First we create the following folder structure::

    flask-sqlite3/
        flaskext/
            __init__.py
            sqlite3.py
        setup.py
        LICENSE

Here's the contents of the most important files:

flaskext/__init__.py
````````````````````

The only purpose of this file is to mark the package as namespace package.
This is required so that multiple modules from different PyPI packages can
reside in the same Python package::

    __import__('pkg_resources').declare_namespace(__name__)

If you want to know exactly what is happening there, checkout the
distribute or setuptools docs which explain how this works.

Just make sure to not put anything else in there!

setup.py
````````

The next file that is absolutely required is the `setup.py` file which is
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
        packages=['flaskext'],
        namespace_packages=['flaskext'],
        zip_safe=False,
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
extensions and adapt.  This is also what the wizard creates for you if you
use it.

flaskext/sqlite3.py
```````````````````

Now this is where your extension code goes.  But how exactly should such
an extension look like?  What are the best practices?  Continue reading
for some insight.

Initializing Extensions
-----------------------

Many extensions will need some kind of initialization step.  For example,
consider your application is currently connecting to SQLite like the
documentation suggests (:ref:`sqlite3`) you'll need to provide some way to
connect to the database and close the connection via an after request handler.
So how does the extension know the name of the application object?

Quite simple: you pass it to it.

There are two recommended ways for an extension to initialize:

initialization functions:
    If your extension is called `helloworld` you might have a function
    called ``init_helloworld(app[, extra_args])`` that initializes the
    extension for that application.  It could attach before / after
    handlers etc.

classes:
    Classes work mostly like initialization functions but can later be
    used to further change the behaviour.  For an example look at how the
    `OAuth extension`_ works: there is an `OAuth` object that provides
    some helper functions like `OAuth.remote_app` to create a reference to
    a remote application that uses OAuth.

What to use depends on what you have in mind.  For the SQLite 3 extension
we will use the class based approach because it will provide users with a
manager object that handles opening and closing database connections.

The Extension Code
------------------

Here's the contents of the `flaskext/sqlite3.py` for copy/paste::

    from __future__ import absolute_import
    import sqlite3

    class SQLite3(object):

        def __init__(self, app):
            self.app = app
            self.app.config.setdefault('SQLITE3_DATABASE', ':memory:')
            self.app.after_request(self.after_request_handler)
            self.db = sqlite3.connect(app.config['SQLITE3_DATABASE'])

        def after_request_handler(self, response):
            self.db.close()
            return response

So here's what these lines of code do:

1.  The ``__future__`` import is necessary to activate absolute imports.
    Otherwise we could not call our module `sqlite3.py` and import the
    top-level `sqlite3` module which actually implements the connection to
    SQLite.
2.  We create a class for our extension that requires a supplied `app` object.
3.  A default configuration for the database is set if it's not there
    (:meth:`dict.setdefault`).
4.  Then we attach an `after_request` handler that is responsible for closing
    our database connection.
5.  We open a database connection and bind it to `self.db`.
6.  Finally, we define the `after_request_handler` passed to `after_request`
    above.

So why did we decide on a class based approach here?  Because using that
extension looks something like this::

    from flask import Flask, g
    from flaskext.sqlite3 import SQLite3

    app = Flask(__name__)
    app.config.from_pyfile('the-config.cfg')
    manager = SQLite(app)
    db = manager.db

You can then use the database from views like this::

    @app.route('/')
    def show_all():
        cur = db.cursor()
        cur.execute(...)

Opening a database connection from outside a view function is simple.

>>> from yourapplication import db
>>> con = db.connect()
>>> cur = con.cursor()

Database Connections and the `g` Object
---------------------------------------

You may be tempted to open a connection to the database and then attach that
connection to the `g` object, perhaps as `g.db`, via a `before_request`
handler. This practice is strongly discouraged. In certain situations - for
instance, when running a shell via the `Flask-Script Extension`_ -
`before_request` will not have run and your database connection will be
unavailable.

.. _Flask-Script Extension: http://packages.python.org/Flask-Script/

Adding an `init_app` Function
-----------------------------

In practice, you'll almost always want to permit users to initialize your
extension and provide an app object after the fact. This can help avoid
circular import problems when a user is breaking their app into multiple files.
Our extension could add an `init_app` function as follows::

    class SQLite3(object):

        def __init__(self, app=None):
            if app is not None:
                self.app = app
                self.app.after_request(self.after_request_handler)
                self.init_app(app)
            else:
                self.app = None

        def init_app(self, app):
            app.config.setdefault('SQLITE3_DATABASE', ':memory:')
            self.db = sqlite3.connect(app.config['SQLITE3_DATABASE'])
            return self.db

        def after_request_handler(self, response):
            self.db.close()
            return response

The user could then initialize the extension in one file::

    manager = SQLite3()

and bind their app to the extension in another file::

    db = manager.init_app(app)

Initialization Functions
-----------------------

Alternatively, our extension could also be implemented via initialization functions::

    from __future__ import absolute_import
    import sqlite3

    def init_sqlite3(app):
        app = app
        app.config.setdefault('SQLITE3_DATABASE', ':memory:')
        db = sqlite3.connect(app.config['SQLITE3_DATABASE'])

        @app.after_request
        def after_request_handler(response):
            db.close()
            return response

        return db

Again, the method you choose will depend on your specific needs.

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

1.  An approved Flask extension must provide exactly one package or module
    inside the `flaskext` namespace package.
2.  It must ship a testsuite that can either be invoked with ``make test``
    or ``python setup.py test``.  For testsuites invoked with ``make
    test`` the extension has to ensure that all dependencies for the test
    are installed automatically, in case of ``python setup.py test``
    dependencies for tests alone can be specified in the `setup.py`
    file.  The testsuite also has to be part of the distribution.
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
    `setup.py` file unless a dependency cannot be met because it is not
    available on PyPI.
7.  The extension must have documentation that uses one of the two Flask
    themes for Sphinx documentation.
8.  The setup.py description (and thus the PyPI description) has to
    link to the documentation, website (if there is one) and there
    must be a link to automatically install the development version
    (``PackageName==dev``).
9.  The ``zip_safe`` flag in the setup script must be set to ``False``,
    even if the extension would be safe for zipping.
10. An extension currently has to support Python 2.5, 2.6 as well as
    Python 2.7


.. _Flask Extension Wizard:
   http://github.com/mitsuhiko/flask-extension-wizard
.. _OAuth extension: http://packages.python.org/Flask-OAuth/
.. _mailinglist: http://flask.pocoo.org/mailinglist/
.. _IRC channel: http://flask.pocoo.org/community/irc/
