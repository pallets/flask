View Decorators
===============

Python has a really interesting feature called function decorators.  This
allows some really neat things for web applications.  Because each view in
Flask is a function, decorators can be used to inject additional
functionality to one or more functions.  The :meth:`~flask.Flask.route`
decorator is the one you probably used already.  But there are use cases
for implementing your own decorator.  For instance, imagine you have a
view that should only be used by people that are logged in.  If a user
goes to the site and is not logged in, they should be redirected to the
login page.  This is a good example of a use case where a decorator is an
excellent solution.

Login Required Decorator
------------------------

So let's implement such a decorator.  A decorator is a function that
wraps and replaces another function.  Since the original function is
replaced, you need to remember to copy the original function's information
to the new function.  Use :func:`functools.wraps` to handle this for you.

This example assumes that the login page is called ``'login'`` and that
the current user is stored in ``g.user`` and is ``None`` if there is no-one
logged in. ::

    from functools import wraps
    from flask import g, request, redirect, url_for

    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if g.user is None:
                return redirect(url_for('login', next=request.url))
            return f(*args, **kwargs)
        return decorated_function

To use the decorator, apply it as innermost decorator to a view function.
When applying further decorators, always remember
that the :meth:`~flask.Flask.route` decorator is the outermost. ::

    @app.route('/secret_page')
    @login_required
    def secret_page():
        pass

.. note::
    The ``next`` value will exist in ``request.args`` after a ``GET`` request for
    the login page.  You'll have to pass it along when sending the ``POST`` request
    from the login form.  You can do this with a hidden input tag, then retrieve it
    from ``request.form`` when logging the user in. ::

        <input type="hidden" value="{{ request.args.get('next', '') }}"/>


Caching Decorator
-----------------

Imagine you have a view function that does an expensive calculation and
because of that you would like to cache the generated results for a
certain amount of time.  A decorator would be nice for that.  We're
assuming you have set up a cache like mentioned in :doc:`caching`.

Here is an example cache function.  It generates the cache key from a
specific prefix (actually a format string) and the current path of the
request.  Notice that we are using a function that first creates the
decorator that then decorates the function.  Sounds awful? Unfortunately
it is a little bit more complex, but the code should still be
straightforward to read.

The decorated function will then work as follows

1. get the unique cache key for the current request based on the current
   path.
2. get the value for that key from the cache. If the cache returned
   something we will return that value.
3. otherwise the original function is called and the return value is
   stored in the cache for the timeout provided (by default 5 minutes).

Here the code::

    from functools import wraps
    from flask import request

    def cached(timeout=5 * 60, key='view/{}'):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                cache_key = key.format(request.path)
                rv = cache.get(cache_key)
                if rv is not None:
                    return rv
                rv = f(*args, **kwargs)
                cache.set(cache_key, rv, timeout=timeout)
                return rv
            return decorated_function
        return decorator

Notice that this assumes an instantiated ``cache`` object is available, see
:doc:`caching`.


Templating Decorator
--------------------

A common pattern invented by the TurboGears guys a while back is a
templating decorator.  The idea of that decorator is that you return a
dictionary with the values passed to the template from the view function
and the template is automatically rendered.  With that, the following
three examples do exactly the same::

    @app.route('/')
    def index():
        return render_template('index.html', value=42)

    @app.route('/')
    @templated('index.html')
    def index():
        return dict(value=42)

    @app.route('/')
    @templated()
    def index():
        return dict(value=42)

As you can see, if no template name is provided it will use the endpoint
of the URL map with dots converted to slashes + ``'.html'``.  Otherwise
the provided template name is used.  When the decorated function returns,
the dictionary returned is passed to the template rendering function.  If
``None`` is returned, an empty dictionary is assumed, if something else than
a dictionary is returned we return it from the function unchanged.  That
way you can still use the redirect function or return simple strings.

Here is the code for that decorator::

    from functools import wraps
    from flask import request, render_template

    def templated(template=None):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                template_name = template
                if template_name is None:
                    template_name = f"'{request.endpoint.replace('.', '/')}.html'"
                ctx = f(*args, **kwargs)
                if ctx is None:
                    ctx = {}
                elif not isinstance(ctx, dict):
                    return ctx
                return render_template(template_name, **ctx)
            return decorated_function
        return decorator


Endpoint Decorator
------------------

When you want to use the werkzeug routing system for more flexibility you
need to map the endpoint as defined in the :class:`~werkzeug.routing.Rule`
to a view function. This is possible with this decorator. For example::

    from flask import Flask
    from werkzeug.routing import Rule

    app = Flask(__name__)
    app.url_map.add(Rule('/', endpoint='index'))

    @app.endpoint('index')
    def my_index():
        return "Hello world"
