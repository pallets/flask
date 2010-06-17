.. _larger-applications:

Larger Applications
===================

For larger applications it's a good idea to use a package instead of a
module.  That is quite simple.  Imagine a small application looks like
this::

    /yourapplication
        /yourapplication.py
        /static
            /style.css
        /templates
            layout.html
            index.html
            login.html
            ...

Simple Packages
---------------

To convert that into a larger one, just create a new folder
`yourapplication` inside the existing one and move everything below it.
Then rename `yourapplication.py` to `__init__.py`.  (Make sure to delete
all `.pyc` files first, otherwise things would most likely break)

You should then end up with something like that::

    /yourapplication
        /yourapplication
            /__init__.py
            /static
                /style.css
            /templates
                layout.html
                index.html
                login.html
                ...

But how do you run your application now?  The naive ``python
yourapplication/__init__.py`` will not work.  Let's just say that Python
does not want modules in packages to be the startup file.  But that is not
a big problem, just add a new file called `runserver.py` next to the inner
`yourapplication` folder with the following contents::

    from yourapplication import app
    app.run(debug=True)

What did we gain from this?  Now we can restructure the application a bit
into multiple modules.  The only thing you have to remember is the
following quick checklist:

1. the `Flask` application object creation has to be in the
   `__init__.py` file.  That way each module can import it safely and the
   `__name__` variable will resolve to the correct package.
2. all the view functions (the ones with a :meth:`~flask.Flask.route`
   decorator on top) have to be imported when in the `__init__.py` file.
   Not the object itself, but the module it is in.  Do the importing at
   the *bottom* of the file.

Here's an example `__init__.py`::

    from flask import Flask
    app = Flask(__name__)

    import yourapplication.views

And this is what `views.py` would look like::

    from yourapplication import app

    @app.route('/')
    def index():
        return 'Hello World!'

You should then end up with something like that::

    /yourapplication
        /yourapplication
            /__init__.py
            /views.py
            /static
                /style.css
            /templates
                layout.html
                index.html
                login.html
                ...

.. admonition:: Circular Imports

   Every Python programmer hates them, and yet we just added some:
   circular imports (That's when two modules depend on each other.  In this
   case `views.py` depends on `__init__.py`).  Be advised that this is a
   bad idea in general but here it is actually fine.  The reason for this is
   that we are not actually using the views in `__init__.py` and just
   ensuring the module is imported and we are doing that at the bottom of
   the file.

   There are still some problems with that approach but if you want to use
   decorators there is no way around that.  Check out the
   :ref:`becomingbig` section for some inspiration how to deal with that.


.. _working-with-modules:

Working with Modules
--------------------

For larger applications with more than a dozen views it makes sense to
split the views into modules.  First let's look at the typical structure of
such an application::

    /yourapplication
        /yourapplication
            /__init__.py
            /views
                __init__.py
                admin.py
                frontend.py
            /static
                /style.css
            /templates
                layout.html
                index.html
                login.html
                ...

The views are stored in the `yourapplication.views` package.  Just make
sure to place an empty `__init__.py` file in there.  Let's start with the
`admin.py` file in the view package.

First we have to create a :class:`~flask.Module` object with the name of
the package.  This works very similar to the :class:`~flask.Flask` object
you have already worked with, it just does not support all of the methods,
but most of them are the same.

Long story short, here's a nice and concise example::

    from flask import Module

    admin = Module(__name__)

    @admin.route('/')
    def index():
        pass

    @admin.route('/login')
    def login():
        pass

    @admin.route('/logout')
    def logout():
        pass

Do the same with the `frontend.py` and then make sure to register the
modules in the application (`__init__.py`) like this::

    from flask import Flask
    from yourapplication.views.admin import admin
    from yourapplication.views.frontend import frontend

    app = Flask(__name__)
    app.register_module(admin)
    app.register_module(frontend)

So what is different when working with modules?  It mainly affects URL
generation.  Remember the :func:`~flask.url_for` function?  When not
working with modules it accepts the name of the function as first
argument.  This first argument is called the "endpoint".  When you are
working with modules you can use the name of the function like you did
without, when generating modules from a function or template in the same
module.  If you want to generate the URL to another module, prefix it with
the name of the module and a dot.

Confused?  Let's clear that up with some examples.  Imagine you have a
method in one module (say `admin`) and you want to redirect to a
different module (say `frontend`).  This would look like this::

    @admin.route('/to_frontend')
    def to_frontend():
        return redirect(url_for('frontend.index'))

    @frontend.route('/')
    def index():
        return "I'm the frontend index"

Now let's say we only want to redirect to a different function in the same
module.  Then we can either use the full qualified endpoint name like we
did in the example above, or we just use the function name::

    @frontend.route('/to_index')
    def to_index():
        return redirect(url_for('index'))

    @frontend.route('/')
    def index():
        return "I'm the index"
