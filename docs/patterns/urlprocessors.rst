Using URL Processors
====================

.. versionadded:: 0.7

Flask 0.7 introduces the concept of URL processors.  The idea is that you
might have a bunch of resources with common parts in the URL that you
don't always explicitly want to provide.  For instance you might have a
bunch of URLs that have the language code in it but you don't want to have
to handle it in every single function yourself.

URL processors are especially helpful when combined with blueprints.  We
will handle both application specific URL processors here as well as
blueprint specifics.

Internationalized Application URLs
----------------------------------

Consider an application like this::

    from flask import Flask, g

    app = Flask(__name__)

    @app.route('/<lang_code>/')
    def index(lang_code):
        g.lang_code = lang_code
        ...

    @app.route('/<lang_code>/about')
    def about(lang_code):
        g.lang_code = lang_code
        ...

This is an awful lot of repetition as you have to handle the language code
setting on the :data:`~flask.g` object yourself in every single function.
Sure, a decorator could be used to simplify this, but if you want to
generate URLs from one function to another you would have to still provide
the language code explicitly which can be annoying.

For the latter, this is where :func:`~flask.Flask.url_defaults` functions
come in.  They can automatically inject values into a call for
:func:`~flask.url_for` automatically.  The code below checks if the
language code is not yet in the dictionary of URL values and if the
endpoint wants a value named ``'lang_code'``::

    @app.url_defaults
    def add_language_code(endpoint, values):
        if 'lang_code' in values or not g.lang_code:
            return
        if app.url_map.is_endpoint_expecting(endpoint, 'lang_code'):
            values['lang_code'] = g.lang_code

The method :meth:`~werkzeug.routing.Map.is_endpoint_expecting` of the URL
map can be used to figure out if it would make sense to provide a language
code for the given endpoint.

The reverse of that function are
:meth:`~flask.Flask.url_value_preprocessor`\s.  They are executed right
after the request was matched and can execute code based on the URL
values.  The idea is that they pull information out of the values
dictionary and put it somewhere else::

    @app.url_value_preprocessor
    def pull_lang_code(endpoint, values):
        g.lang_code = values.pop('lang_code', None)

That way you no longer have to do the `lang_code` assignment to
:data:`~flask.g` in every function.  You can further improve that by
writing your own decorator that prefixes URLs with the language code, but
the more beautiful solution is using a blueprint.  Once the
``'lang_code'`` is popped from the values dictionary and it will no longer
be forwarded to the view function reducing the code to this::

    from flask import Flask, g

    app = Flask(__name__)

    @app.url_defaults
    def add_language_code(endpoint, values):
        if 'lang_code' in values or not g.lang_code:
            return
        if app.url_map.is_endpoint_expecting(endpoint, 'lang_code'):
            values['lang_code'] = g.lang_code

    @app.url_value_preprocessor
    def pull_lang_code(endpoint, values):
        g.lang_code = values.pop('lang_code', None)

    @app.route('/<lang_code>/')
    def index():
        ...

    @app.route('/<lang_code>/about')
    def about():
        ...

Internationalized Blueprint URLs
--------------------------------

Because blueprints can automatically prefix all URLs with a common string
it's easy to automatically do that for every function.  Furthermore
blueprints can have per-blueprint URL processors which removes a whole lot
of logic from the :meth:`~flask.Flask.url_defaults` function because it no
longer has to check if the URL is really interested in a ``'lang_code'``
parameter::

    from flask import Blueprint, g

    bp = Blueprint('frontend', __name__, url_prefix='/<lang_code>')

    @bp.url_defaults
    def add_language_code(endpoint, values):
        values.setdefault('lang_code', g.lang_code)

    @bp.url_value_preprocessor
    def pull_lang_code(endpoint, values):
        g.lang_code = values.pop('lang_code')

    @bp.route('/')
    def index():
        ...

    @bp.route('/about')
    def about():
        ...
