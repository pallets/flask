Templates
=========

Flask leverages Jinja as its template engine.  You are free to use
a different template engine, but you still have to install Jinja to run
Flask itself.  This requirement is necessary to enable rich extensions.
An extension can depend on Jinja being present.

Note: Flask's template rendering behavior is explained in more detail in the official Jinja documentation linked below.

This section only gives a very quick introduction into how Jinja
is integrated into Flask.  If you want information on the template
engine's syntax itself, head over to the official `Jinja Template
Documentation <https://jinja.palletsprojects.com/templates/>`_ for
more information.

Jinja Setup
-----------

Flask sets up Jinja with some default behavior to keep templates safe and easy to work with:

- When rendering templates with :func:`~flask.templating.render_template`, autoescaping
  is turned on for files ending in ``.html``, ``.htm``, ``.xml``, ``.xhtml`` and ``.svg``.
  This avoids accidental HTML or XML injection.

- With :func:`~flask.templating.render_template_string`, all output is autoescaped
  since there is no file extension to determine behavior.

- Templates can turn autoescaping on or off using the ``{% autoescape %}`` block when
  more control is needed.

- Flask also adds a few helpful global utilities to the Jinja context so they can be
  used directly in templates without extra setup.

Standard Context
----------------

The following global variables are available within Jinja templates
by default:

.. data:: config
   :noindex:

   The current configuration object (:data:`flask.Flask.config`)

   .. versionadded:: 0.6

   .. versionchanged:: 0.10
      This is now always available, even in imported templates.

.. data:: request
   :noindex:

   The current request object (:class:`flask.request`).  This variable is
   unavailable if the template was rendered without an active request
   context.

.. data:: session
   :noindex:

   The current session object (:class:`flask.session`).  This variable
   is unavailable if the template was rendered without an active request
   context.

.. data:: g
   :noindex:

   The request-bound object for global variables (:data:`flask.g`).  This
   variable is unavailable if the template was rendered without an active
   request context.

Using `url_for` in Templates
----------------------------

Flask provides the `url_for` function to dynamically build URLs based on the names of view functions instead of hard-coding paths directly in templates. This allows your application to remain maintainable and flexible as route definitions evolve. When route paths are modified or moved, templates using `url_for` will continue to work without requiring any changes.

Consider the following view function:

.. code-block:: python

    @app.route('/user/<username>')
    def profile(username):
        return f"Profile: {username}"

Inside a Jinja template, the corresponding link can be generated with:

.. code-block:: html

    <a href="{{ url_for('profile', username='alice') }}">View Profile</a>

This will render to:

.. code-block:: text

    /user/alice

Using `url_for` is recommended over hard-coded links such as `/user/alice`, because it keeps the routing logic and template usage consistent and reduces the potential for broken links within the application.

Using `url_for` for Static Files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In addition to generating links for dynamic routes, `url_for` can also be used to reference static assets such as images, stylesheets, or JavaScript files. Flask makes files located inside the ``static`` directory available under the ``static`` endpoint.

Example usage in a template:

.. code-block:: html

    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">

This ensures that static file references remain valid even when configured to serve from a different location, a CDN, or when additional cache-busting strategies are applied.

.. function:: url_for(endpoint, **values)
   :noindex:

   Builds a URL to a given endpoint. Commonly used to link to routes or static files
   directly from templates.

.. function:: get_flashed_messages(with_categories=False, category_filter=())
   :noindex:

   Retrieves flash messages that were stored during the request cycle for display
   in templates.

.. admonition:: The Jinja Context Behavior

   These variables are added to the context of variables, they are not
   global variables.  The difference is that by default these will not
   show up in the context of imported templates.  This is partially caused
   by performance considerations, partially to keep things explicit.

   What does this mean for you?  If you have a macro you want to import,
   that needs to access the request object you have two possibilities:

   1.   you explicitly pass the request to the macro as parameter, or
        the attribute of the request object you are interested in.
   2.   you import the macro "with context".

   Importing with context looks like this:

   .. sourcecode:: jinja

      {% from '_helpers.html' import my_macro with context %}

Controlling Autoescaping
------------------------

Autoescaping is the concept of automatically escaping special characters
for you.  Special characters in the sense of HTML (or XML, and thus XHTML)
are ``&``, ``>``, ``<``, ``"`` as well as ``'``.  Because these characters
carry specific meanings in documents on their own you have to replace them
by so called "entities" if you want to use them for text.  Not doing so
would not only cause user frustration by the inability to use these
characters in text, but can also lead to security problems.  (see
:ref:`security-xss`)

Sometimes however you will need to disable autoescaping in templates.
This can be the case if you want to explicitly inject HTML into pages, for
example if they come from a system that generates secure HTML like a
markdown to HTML converter.

There are three ways to accomplish that:

-   In the Python code, wrap the HTML string in a :class:`~markupsafe.Markup`
    object before passing it to the template.  This is in general the
    recommended way.
-   Inside the template, use the ``|safe`` filter to explicitly mark a
    string as safe HTML (``{{ myvariable|safe }}``)
-   Temporarily disable the autoescape system altogether.

To disable the autoescape system in templates, you can use the ``{%
autoescape %}`` block:

.. sourcecode:: html+jinja

    {% autoescape false %}
        <p>autoescaping is disabled here
        <p>{{ will_not_be_escaped }}
    {% endautoescape %}

Whenever you do this, please be very cautious about the variables you are
using in this block.

.. _registering-filters:

Registering Filters, Tests, and Globals
---------------------------------------

The Flask app and blueprints provide decorators and methods to register your own
filters, tests, and global functions for use in Jinja templates. They all follow
the same pattern, so the following examples only discuss filters.

Decorate a function with :meth:`~.Flask.template_filter` to register it as a
template filter.

.. code-block:: python

    @app.template_filter
    def reverse(s):
        return reversed(s)

.. code-block:: jinja

    {% for item in data | reverse %}
    {% endfor %}

By default it will use the name of the function as the name of the filter, but
that can be changed by passing a name to the decorator.

.. code-block:: python

    @app.template_filter("reverse")
    def reverse_filter(s):
        return reversed(s)

A filter can be registered separately using :meth:`~.Flask.add_template_filter`.
The name is optional and will use the function name if not given.

.. code-block:: python

    def reverse_filter(s):
        return reversed(s)

    app.add_template_filter(reverse_filter, "reverse")

For template tests, use the :meth:`~.Flask.template_test` decorator or
:meth:`~.Flask.add_template_test` method. For template global functions, use the
:meth:`~.Flask.template_global` decorator or :meth:`~.Flask.add_template_global`
method.

The same methods also exist on :class:`.Blueprint`, prefixed with ``app_`` to
indicate that the registered functions will be available to all templates, not
only when rendering from within the blueprint.

The Jinja environment is also available as :attr:`~.Flask.jinja_env`. It may be
modified directly, as you would when using Jinja outside Flask.

Context Processors
------------------

To inject new variables automatically into the context of a template,
context processors exist in Flask.  Context processors run before the
template is rendered and have the ability to inject new values into the
template context.  A context processor is a function that returns a
dictionary.  The keys and values of this dictionary are then merged with
the template context, for all templates in the app::

Example: Injecting a User Object
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    @app.context_processor
    def inject_user():
        return dict(user=g.user)

The context processor above makes a variable called `user` available in
the template with the value of `g.user`.  This example is not very
interesting because `g` is available in templates anyways, but it gives an
idea how this works.

Variables are not limited to values; a context processor can also make
functions available to templates (since Python allows passing around
functions)::

Example: Registering a Utility Function
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    @app.context_processor
    def utility_processor():
        def format_price(amount, currency="€"):
            return f"{amount:.2f}{currency}"
        return dict(format_price=format_price)

The context processor above makes the `format_price` function available to all
templates::

    {{ format_price(0.33) }}

You could also build `format_price` as a template filter (see
:ref:`registering-filters`), but this demonstrates how to pass functions in a
context processor.

Streaming
---------

Rather than rendering the entire template into a single large string, it can be
rendered in smaller pieces and returned as a stream. This allows the application
to send partial output to the client sooner.

Streaming can be helpful in scenarios such as:

- improving initial page load times by sending HTML chunks as they are ready
- reducing memory usage when working with very large templates

Streaming Templates
^^^^^^^^^^^^^^^^^^^

Jinja allows templates to be rendered incrementally, producing a stream of
string fragments instead of a single consolidated output. This enables
applications to send partial responses as they become available.

Flask exposes helpers to simplify streamed rendering:

- :func:`~flask.stream_template` — streams a template file.
- :func:`~flask.stream_template_string` — streams a template given as a string.

.. code-block:: python

    from flask import stream_template

    @app.get("/timeline")
    def timeline():
        return stream_template("timeline.html")

Function Behavior
^^^^^^^^^^^^^^^^^
When a request is active, these functions automatically apply the :func:`~flask.stream_with_context` wrapper, ensuring the request context remains available in the template.
