.. _blueprints:

Modular Applications with Blueprints
====================================

.. versionadded:: 0.7

Flask knows a concept known as “blueprints” which can greatly simplify how
large applications work.  A blueprint is an object works similar to an
actual :class:`Flask` application object, but it is not actually an
application.  Rather it is the blueprint of how to create an application.
Think of it like that: you might want to have an application that has a
wiki.  So what you can do is creating the blueprint for a wiki and then
let the application assemble the wiki on the application object.

Why Blueprints?
---------------

Why have blueprints and not multiple application objects?  The utopia of
pluggable applications are different WSGI applications and merging them
together somehow.  You can do that (see :ref:`app-dispatch`) but it's not
the right tool for every case.  Having different applications means having
different configs.  Applications are also separated on the WSGI layer
which is a lot lower level than the level that Flask usually operates on
where you have request and response objects.

Blueprints do not necessarily have to implement applications.  They could
only provide filters for templates, static files, templates or similar
things.  They share the same config as the application and can change the
application as necessary when being registered.

The downside is that you cannot unregister a blueprint once application
without having to destroy the whole application object.

The Concept of Blueprints
-------------------------

The basic concept of blueprints is that they record operations that should
be executed when the blueprint is registered on the application.  However
additionally each time a request gets dispatched to a view that was
declared to a blueprint Flask will remember that the request was
dispatched to that blueprint.  That way it's easier to generate URLs from
one endpoint to another in the same module.

My First Blueprint
------------------

This is what a very basic blueprint looks like.  In this case we want to
implement a blueprint that does simple rendering of static templates::

    from flask import Blueprint, render_template, abort
    from jinja2 import TemplateNotFound

    simple_page = Blueprint('simple_page', __name__)

    @simple_page.route('/', defaults={'page': 'index'})
    @simple_page.route('/<page>')
    def show(page):
        try:
            return render_template('pages/%s.html' % page)
        except TemplateNotFound:
            abort(404)

When you bind a function with the help of the ``@simple_page.route``
decorator the blueprint will record the intention of registering the
function `show` on the application when it's later registered.
Additionally it will prefix the endpoint of the function with the
name of the blueprint which was given to the :class:`Blueprint`
constructor (in this case also ``simple_page``).

Registering Blueprints
----------------------

So how do you register that blueprint?  Like this::

    from flask import Flask
    from yourapplication.simple_page import simple_page

    app = Flask(__name__)
    app.register_blueprint(simple_page)

If you check the rules registered on the application, you will find
these::

    [<Rule '/static/<filename>' (HEAD, OPTIONS, GET) -> static>,
     <Rule '/<page>' (HEAD, OPTIONS, GET) -> simple_page.show>,
     <Rule '/' (HEAD, OPTIONS, GET) -> simple_page.show>]

The first one is obviously from the application ifself for the static
files.  The other two are for the `show` function of the ``simple_page``
blueprint.  As you can see, they are also prefixed with the name of the
blueprint and separated by a dot (``.``).

Blueprints however can also be mounted at different locations::

    app.register_blueprint(simple_page, url_prefix='/pages')

And sure enough, these are the generated rules::

    [<Rule '/static/<filename>' (HEAD, OPTIONS, GET) -> static>,
     <Rule '/pages/<page>' (HEAD, OPTIONS, GET) -> simple_page.show>,
     <Rule '/pages/' (HEAD, OPTIONS, GET) -> simple_page.show>]

On top of that you can register blueprints multiple times though not every
blueprint might respond properly to that.  In fact it depends on how the
blueprint is implemented if it can be mounted more than once.

Blueprint Resources
-------------------

Blueprints can provide resources as well.  Sometimes you might want to
introduce a blueprint only for the resources it provides.

Blueprint Resource Folder
`````````````````````````

Like for regular applications, blueprints are considered to be contained
in a folder.  While multiple blueprints can origin from the same folder,
it does not have to be the case and it's usually not recommended.

The folder is infered from the second argument to :class:`Blueprint` which
is ususally `__name__`.  This argument specifies what logical Python
module or package corresponds to the blueprint.  If it points to an actual
Python package that package (which is a folder on the filesystem) is the
resource folder.  If it's a module, the package the module is contained in
will be the resource folder.  You can access the
:attr:`Blueprint.root_path` property to see what's the resource folder::

    >>> simple_page.root_path
    '/Users/username/TestProject/yourapplication'

To quickly open sources from this folder you can use the
:meth:`~Blueprint.open_resource` function::

    with simple_page.open_resource('static/style.css') as f:
        code = f.read()

Static Files
````````````

A blueprint can expose a folder with static files by providing a path to a
folder on the filesystem via the `static_folder` keyword argument.  It can
either be an absolute path or one relative to the folder of the
blueprint::

    admin = Blueprint('admin', __name__, static_folder='static')

By default the rightmost part of the path is where it is exposed on the
web.  Because the folder is called ``static`` here it will be available at
the location of the blueprint + ``/static``.  Say the blueprint is
registered for ``/admin`` the static folder will be at ``/admin/static``.

The endpoint is named `blueprint_name.static` so you can generate URLs to
it like you would do to the static folder of the application::

    url_for('admin.static', filename='style.css')

Templates
`````````

If you want the blueprint to expose templates you can do that by providing
the `template_folder` parameter to the :class:`Blueprint` constructor::

    admin = Blueprint('admin', __name__, template_folder='templates')

As for static files, the path can be absolute or relative to the blueprint
resource folder.  The template folder is added to the searchpath of
templates but with a lower priority than the actual application's template
folder.  That way you can easily override templates that a blueprint
provides in the actual application.

So if you have a blueprint in the folder ``yourapplication/admin`` and you
want to render the template ``'admin/index.html'`` and you have provided
``templates`` as a `template_folder` you will have to create a file like
this: ``yourapplication/admin/templates/admin/index.html``.

Building URLs
-------------

If you want to link from one page to another you can use the
:func:`url_for` function just like you normally would do just that you
prefix the URL endpoint with the name of the blueprint and a dot (``.``)::

    url_for('admin.index')

Additionally if you are in a view function of a blueprint or a rendered
template and you want to link to another endpoint of the same blueprint,
you can use relative redirects by prefixing the endpoint with a dot only::

    url_for('.index')

This will link to ``admin.index`` for instance in case the current request
was dispatched to any other admin blueprint endpoint.
