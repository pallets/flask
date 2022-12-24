Flask Extension Development
===========================

.. currentmodule:: flask

Extensions are extra packages that add functionality to a Flask
application. While `PyPI`_ contains many Flask extensions, you may not
find one that fits your need. If this is the case, you can create your
own, and publish it for others to use as well.

This guide will show how to create a Flask extension, and some of the
common patterns and requirements involved. Since extensions can do
anything, this guide won't be able to cover every possibility.

The best ways to learn about extensions are to look at how other
extensions you use are written, and discuss with others. Discuss your
design ideas with others on our `Discord Chat`_ or
`GitHub Discussions`_.

The best extensions share common patterns, so that anyone familiar with
using one extension won't feel completely lost with another. This can
only work if collaboration happens early.


Naming
------

A Flask extension typically has ``flask`` in its name as a prefix or
suffix. If it wraps another library, it should include the library name
as well. This makes it easy to search for extensions, and makes their
purpose clearer.

A general Python packaging recommendation is that the install name from
the package index and the name used in ``import`` statements should be
related. The import name is lowercase, with words separated by
underscores (``_``). The install name is either lower case or title
case, with words separated by dashes (``-``). If it wraps another
library, prefer using the same case as that library's name.

Here are some example install and import names:

-   ``Flask-Name`` imported as ``flask_name``
-   ``flask-name-lower`` imported as ``flask_name_lower``
-   ``Flask-ComboName`` imported as ``flask_comboname``
-   ``Name-Flask`` imported as ``name_flask``


The Extension Class and Initialization
--------------------------------------

All extensions will need some entry point that initializes the
extension with the application. The most common pattern is to create a
class that represents the extension's configuration and behavior, with
an ``init_app`` method to apply the extension instance to the given
application instance.

.. code-block:: python

    class HelloExtension:
        def __init__(self, app=None):
            if app is not None:
                self.init_app(app)

        def init_app(self, app):
            app.before_request(...)

It is important that the app is not stored on the extension, don't do
``self.app = app``. The only time the extension should have direct
access to an app is during ``init_app``, otherwise it should use
:data:`current_app`.

This allows the extension to support the application factory pattern,
avoids circular import issues when importing the extension instance
elsewhere in a user's code, and makes testing with different
configurations easier.

.. code-block:: python

    hello = HelloExtension()

    def create_app():
        app = Flask(__name__)
        hello.init_app(app)
        return app

Above, the ``hello`` extension instance exists independently of the
application. This means that other modules in a user's project can do
``from project import hello`` and use the extension in blueprints before
the app exists.

The :attr:`Flask.extensions` dict can be used to store a reference to
the extension on the application, or some other state specific to the
application. Be aware that this is a single namespace, so use a name
unique to your extension, such as the extension's name without the
"flask" prefix.


Adding Behavior
---------------

There are many ways that an extension can add behavior. Any setup
methods that are available on the :class:`Flask` object can be used
during an extension's ``init_app`` method.

A common pattern is to use :meth:`~Flask.before_request` to initialize
some data or a connection at the beginning of each request, then
:meth:`~Flask.teardown_request` to clean it up at the end. This can be
stored on :data:`g`, discussed more below.

A more lazy approach is to provide a method that initializes and caches
the data or connection. For example, a ``ext.get_db`` method could
create a database connection the first time it's called, so that a view
that doesn't use the database doesn't create a connection.

Besides doing something before and after every view, your extension
might want to add some specific views as well. In this case, you could
define a :class:`Blueprint`, then call :meth:`~Flask.register_blueprint`
during ``init_app`` to add the blueprint to the app.


Configuration Techniques
------------------------

There can be multiple levels and sources of configuration for an
extension. You should consider what parts of your extension fall into
each one.

-   Configuration per application instance, through ``app.config``
    values. This is configuration that could reasonably change for each
    deployment of an application. A common example is a URL to an
    external resource, such as a database. Configuration keys should
    start with the extension's name so that they don't interfere with
    other extensions.
-   Configuration per extension instance, through ``__init__``
    arguments. This configuration usually affects how the extension
    is used, such that it wouldn't make sense to change it per
    deployment.
-   Configuration per extension instance, through instance attributes
    and decorator methods. It might be more ergonomic to assign to
    ``ext.value``, or use a ``@ext.register`` decorator to register a
    function, after the extension instance has been created.
-   Global configuration through class attributes. Changing a class
    attribute like ``Ext.connection_class`` can customize default
    behavior without making a subclass. This could be combined
    per-extension configuration to override defaults.
-   Subclassing and overriding methods and attributes. Making the API of
    the extension itself something that can be overridden provides a
    very powerful tool for advanced customization.

The :class:`~flask.Flask` object itself uses all of these techniques.

It's up to you to decide what configuration is appropriate for your
extension, based on what you need and what you want to support.

Configuration should not be changed after the application setup phase is
complete and the server begins handling requests. Configuration is
global, any changes to it are not guaranteed to be visible to other
workers.


Data During a Request
---------------------

When writing a Flask application, the :data:`~flask.g` object is used to
store information during a request. For example the
:doc:`tutorial <tutorial/database>` stores a connection to a SQLite
database as ``g.db``. Extensions can also use this, with some care.
Since ``g`` is a single global namespace, extensions must use unique
names that won't collide with user data. For example, use the extension
name as a prefix, or as a namespace.

.. code-block:: python

    # an internal prefix with the extension name
    g._hello_user_id = 2

    # or an internal prefix as a namespace
    from types import SimpleNamespace
    g._hello = SimpleNamespace()
    g._hello.user_id = 2

The data in ``g`` lasts for an application context. An application
context is active when a request context is, or when a CLI command is
run. If you're storing something that should be closed, use
:meth:`~flask.Flask.teardown_appcontext` to ensure that it gets closed
when the application context ends. If it should only be valid during a
request, or would not be used in the CLI outside a request, use
:meth:`~flask.Flask.teardown_request`.


Views and Models
----------------

Your extension views might want to interact with specific models in your
database, or some other extension or data connected to your application.
For example, let's consider a ``Flask-SimpleBlog`` extension that works
with Flask-SQLAlchemy to provide a ``Post`` model and views to write
and read posts.

The ``Post`` model needs to subclass the Flask-SQLAlchemy ``db.Model``
object, but that's only available once you've created an instance of
that extension, not when your extension is defining its views. So how
can the view code, defined before the model exists, access the model?

One method could be to use :doc:`views`. During ``__init__``, create
the model, then create the views by passing the model to the view
class's :meth:`~views.View.as_view` method.

.. code-block:: python

    class PostAPI(MethodView):
        def __init__(self, model):
            self.model = model

        def get(self, id):
            post = self.model.query.get(id)
            return jsonify(post.to_json())

    class BlogExtension:
        def __init__(self, db):
            class Post(db.Model):
                id = db.Column(primary_key=True)
                title = db.Column(db.String, nullable=False)

            self.post_model = Post

        def init_app(self, app):
            api_view = PostAPI.as_view(model=self.post_model)

    db = SQLAlchemy()
    blog = BlogExtension(db)
    db.init_app(app)
    blog.init_app(app)

Another technique could be to use an attribute on the extension, such as
``self.post_model`` from above. Add the extension to ``app.extensions``
in ``init_app``, then access
``current_app.extensions["simple_blog"].post_model`` from views.

You may also want to provide base classes so that users can provide
their own ``Post`` model that conforms to the API your extension
expects. So they could implement ``class Post(blog.BasePost)``, then
set it as ``blog.post_model``.

As you can see, this can get a bit complex. Unfortunately, there's no
perfect solution here, only different strategies and tradeoffs depending
on your needs and how much customization you want to offer. Luckily,
this sort of resource dependency is not a common need for most
extensions. Remember, if you need help with design, ask on our
`Discord Chat`_ or `GitHub Discussions`_.


Recommended Extension Guidelines
--------------------------------

Flask previously had the concept of "approved extensions", where the
Flask maintainers evaluated the quality, support, and compatibility of
the extensions before listing them. While the list became too difficult
to maintain over time, the guidelines are still relevant to all
extensions maintained and developed today, as they help the Flask
ecosystem remain consistent and compatible.

1.  An extension requires a maintainer. In the event an extension author
    would like to move beyond the project, the project should find a new
    maintainer and transfer access to the repository, documentation,
    PyPI, and any other services. The `Pallets-Eco`_ organization on
    GitHub allows for community maintenance with oversight from the
    Pallets maintainers.
2.  The naming scheme is *Flask-ExtensionName* or *ExtensionName-Flask*.
    It must provide exactly one package or module named
    ``flask_extension_name``.
3.  The extension must use an open source license. The Python web
    ecosystem tends to prefer BSD or MIT. It must be open source and
    publicly available.
4.  The extension's API must have the following characteristics:

    -   It must support multiple applications running in the same Python
        process. Use ``current_app`` instead of ``self.app``, store
        configuration and state per application instance.
    -   It must be possible to use the factory pattern for creating
        applications. Use the ``ext.init_app()`` pattern.

5.  From a clone of the repository, an extension with its dependencies
    must be installable in editable mode with ``pip install -e .``.
6.  It must ship tests that can be invoked with a common tool like
    ``tox -e py``, ``nox -s test`` or ``pytest``. If not using ``tox``,
    the test dependencies should be specified in a requirements file.
    The tests must be part of the sdist distribution.
7.  A link to the documentation or project website must be in the PyPI
    metadata or the readme. The documentation should use the Flask theme
    from the `Official Pallets Themes`_.
8.  The extension's dependencies should not use upper bounds or assume
    any particular version scheme, but should use lower bounds to
    indicate minimum compatibility support. For example,
    ``sqlalchemy>=1.4``.
9.  Indicate the versions of Python supported using
    ``python_requires=">=version"``. Flask itself supports Python >=3.7
    as of December 2021, but this will update over time.

.. _PyPI: https://pypi.org/search/?c=Framework+%3A%3A+Flask
.. _Discord Chat: https://discord.gg/pallets
.. _GitHub Discussions: https://github.com/pallets/flask/discussions
.. _Official Pallets Themes: https://pypi.org/project/Pallets-Sphinx-Themes/
.. _Pallets-Eco: https://github.com/pallets-eco
