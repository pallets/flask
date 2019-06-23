.. _api:

API
===

.. module:: flask

This part of the documentation covers all the interfaces of Flask.  For
parts where Flask depends on external libraries, we document the most
important right here and provide links to the canonical documentation.


Application Object
------------------

.. autoclass:: Flask
   :members:
   :inherited-members:


Blueprint Objects
-----------------

.. autoclass:: Blueprint
   :members:
   :inherited-members:

Incoming Request Data
---------------------

.. autoclass:: Request
   :members:
   :inherited-members:

   .. attribute:: environ

      The underlying WSGI environment.

   .. attribute:: path
   .. attribute:: full_path
   .. attribute:: script_root
   .. attribute:: url
   .. attribute:: base_url
   .. attribute:: url_root

      Provides different ways to look at the current :rfc:`3987`.
      Imagine your application is listening on the following application
      root::

          http://www.example.com/myapplication

      And a user requests the following URI::

          http://www.example.com/myapplication/%CF%80/page.html?x=y

      In this case the values of the above mentioned attributes would be
      the following:

      ============= ======================================================
      `path`        ``u'/π/page.html'``
      `full_path`   ``u'/π/page.html?x=y'``
      `script_root` ``u'/myapplication'``
      `base_url`    ``u'http://www.example.com/myapplication/π/page.html'``
      `url`         ``u'http://www.example.com/myapplication/π/page.html?x=y'``
      `url_root`    ``u'http://www.example.com/myapplication/'``
      ============= ======================================================


.. attribute:: request

   To access incoming request data, you can use the global `request`
   object.  Flask parses incoming request data for you and gives you
   access to it through that global object.  Internally Flask makes
   sure that you always get the correct data for the active thread if you
   are in a multithreaded environment.

   This is a proxy.  See :ref:`notes-on-proxies` for more information.

   The request object is an instance of a :class:`~werkzeug.wrappers.Request`
   subclass and provides all of the attributes Werkzeug defines.  This
   just shows a quick overview of the most important ones.


Response Objects
----------------

.. autoclass:: flask.Response
   :members: set_cookie, max_cookie_size, data, mimetype, is_json, get_json

   .. attribute:: headers

      A :class:`~werkzeug.datastructures.Headers` object representing the response headers.

   .. attribute:: status

      A string with a response status.

   .. attribute:: status_code

      The response status as integer.


Sessions
--------

If you have set :attr:`Flask.secret_key` (or configured it from
:data:`SECRET_KEY`) you can use sessions in Flask applications. A session makes
it possible to remember information from one request to another. The way Flask
does this is by using a signed cookie. The user can look at the session
contents, but can't modify it unless they know the secret key, so make sure to
set that to something complex and unguessable.

To access the current session you can use the :class:`session` object:

.. class:: session

   The session object works pretty much like an ordinary dict, with the
   difference that it keeps track of modifications.

   This is a proxy.  See :ref:`notes-on-proxies` for more information.

   The following attributes are interesting:

   .. attribute:: new

      ``True`` if the session is new, ``False`` otherwise.

   .. attribute:: modified

      ``True`` if the session object detected a modification.  Be advised
      that modifications on mutable structures are not picked up
      automatically, in that situation you have to explicitly set the
      attribute to ``True`` yourself.  Here an example::

          # this change is not picked up because a mutable object (here
          # a list) is changed.
          session['objects'].append(42)
          # so mark it as modified yourself
          session.modified = True

   .. attribute:: permanent

      If set to ``True`` the session lives for
      :attr:`~flask.Flask.permanent_session_lifetime` seconds.  The
      default is 31 days.  If set to ``False`` (which is the default) the
      session will be deleted when the user closes the browser.


Session Interface
-----------------

.. versionadded:: 0.8

The session interface provides a simple way to replace the session
implementation that Flask is using.

.. currentmodule:: flask.sessions

.. autoclass:: SessionInterface
   :members:

.. autoclass:: SecureCookieSessionInterface
   :members:

.. autoclass:: SecureCookieSession
   :members:

.. autoclass:: NullSession
   :members:

.. autoclass:: SessionMixin
   :members:

.. admonition:: Notice

   The ``PERMANENT_SESSION_LIFETIME`` config key can also be an integer
   starting with Flask 0.8.  Either catch this down yourself or use
   the :attr:`~flask.Flask.permanent_session_lifetime` attribute on the
   app which converts the result to an integer automatically.


Test Client
-----------

.. currentmodule:: flask.testing

.. autoclass:: FlaskClient
   :members:


Test CLI Runner
---------------

.. currentmodule:: flask.testing

.. autoclass:: FlaskCliRunner
    :members:


Application Globals
-------------------

.. currentmodule:: flask

To share data that is valid for one request only from one function to
another, a global variable is not good enough because it would break in
threaded environments.  Flask provides you with a special object that
ensures it is only valid for the active request and that will return
different values for each request.  In a nutshell: it does the right
thing, like it does for :class:`request` and :class:`session`.

.. data:: g

    A namespace object that can store data during an
    :doc:`application context </appcontext>`. This is an instance of
    :attr:`Flask.app_ctx_globals_class`, which defaults to
    :class:`ctx._AppCtxGlobals`.

    This is a good place to store resources during a request. During
    testing, you can use the :ref:`faking-resources` pattern to
    pre-configure such resources.

    This is a proxy. See :ref:`notes-on-proxies` for more information.

    .. versionchanged:: 0.10
        Bound to the application context instead of the request context.

.. autoclass:: flask.ctx._AppCtxGlobals
    :members:


Useful Functions and Classes
----------------------------

.. data:: current_app

    A proxy to the application handling the current request. This is
    useful to access the application without needing to import it, or if
    it can't be imported, such as when using the application factory
    pattern or in blueprints and extensions.

    This is only available when an
    :doc:`application context </appcontext>` is pushed. This happens
    automatically during requests and CLI commands. It can be controlled
    manually with :meth:`~flask.Flask.app_context`.

    This is a proxy. See :ref:`notes-on-proxies` for more information.

.. autofunction:: has_request_context

.. autofunction:: copy_current_request_context

.. autofunction:: has_app_context

.. autofunction:: url_for

.. autofunction:: abort

.. autofunction:: redirect

.. autofunction:: make_response

.. autofunction:: after_this_request

.. autofunction:: send_file

.. autofunction:: send_from_directory

.. autofunction:: safe_join

.. autofunction:: escape

.. autoclass:: Markup
   :members: escape, unescape, striptags

Message Flashing
----------------

.. autofunction:: flash

.. autofunction:: get_flashed_messages

JSON Support
------------

.. module:: flask.json

Flask uses ``simplejson`` for the JSON implementation.  Since simplejson
is provided by both the standard library as well as extension, Flask will
try simplejson first and then fall back to the stdlib json module.  On top
of that it will delegate access to the current application's JSON encoders
and decoders for easier customization.

So for starters instead of doing::

    try:
        import simplejson as json
    except ImportError:
        import json

You can instead just do this::

    from flask import json

For usage examples, read the :mod:`json` documentation in the standard
library.  The following extensions are by default applied to the stdlib's
JSON module:

1.  ``datetime`` objects are serialized as :rfc:`822` strings.
2.  Any object with an ``__html__`` method (like :class:`~flask.Markup`)
    will have that method called and then the return value is serialized
    as string.

The :func:`~htmlsafe_dumps` function of this json module is also available
as a filter called ``|tojson`` in Jinja2.  Note that in versions of Flask prior
to Flask 0.10, you must disable escaping with ``|safe`` if you intend to use
``|tojson`` output inside ``script`` tags. In Flask 0.10 and above, this
happens automatically (but it's harmless to include ``|safe`` anyway).

.. sourcecode:: html+jinja

    <script type=text/javascript>
        doSomethingWith({{ user.username|tojson|safe }});
    </script>

.. admonition:: Auto-Sort JSON Keys

    The configuration variable ``JSON_SORT_KEYS`` (:ref:`config`) can be
    set to false to stop Flask from auto-sorting keys.  By default sorting
    is enabled and outside of the app context sorting is turned on.

    Notice that disabling key sorting can cause issues when using content
    based HTTP caches and Python's hash randomization feature.

.. autofunction:: jsonify

.. autofunction:: dumps

.. autofunction:: dump

.. autofunction:: loads

.. autofunction:: load

.. autoclass:: JSONEncoder
   :members:

.. autoclass:: JSONDecoder
   :members:

.. automodule:: flask.json.tag

Template Rendering
------------------

.. currentmodule:: flask

.. autofunction:: render_template

.. autofunction:: render_template_string

.. autofunction:: get_template_attribute

Configuration
-------------

.. autoclass:: Config
   :members:


Stream Helpers
--------------

.. autofunction:: stream_with_context

Useful Internals
----------------

.. autoclass:: flask.ctx.RequestContext
   :members:

.. data:: _request_ctx_stack

    The internal :class:`~werkzeug.local.LocalStack` that holds
    :class:`~flask.ctx.RequestContext` instances. Typically, the
    :data:`request` and :data:`session` proxies should be accessed
    instead of the stack. It may be useful to access the stack in
    extension code.

    The following attributes are always present on each layer of the
    stack:

    `app`
      the active Flask application.

    `url_adapter`
      the URL adapter that was used to match the request.

    `request`
      the current request object.

    `session`
      the active session object.

    `g`
      an object with all the attributes of the :data:`flask.g` object.

    `flashes`
      an internal cache for the flashed messages.

    Example usage::

        from flask import _request_ctx_stack

        def get_session():
            ctx = _request_ctx_stack.top
            if ctx is not None:
                return ctx.session

.. autoclass:: flask.ctx.AppContext
   :members:

.. data:: _app_ctx_stack

    The internal :class:`~werkzeug.local.LocalStack` that holds
    :class:`~flask.ctx.AppContext` instances. Typically, the
    :data:`current_app` and :data:`g` proxies should be accessed instead
    of the stack. Extensions can access the contexts on the stack as a
    namespace to store data.

    .. versionadded:: 0.9

.. autoclass:: flask.blueprints.BlueprintSetupState
   :members:

.. _core-signals-list:

Signals
-------

.. versionadded:: 0.6

.. data:: signals.signals_available

   ``True`` if the signaling system is available.  This is the case
   when `blinker`_ is installed.

The following signals exist in Flask:

.. data:: template_rendered

   This signal is sent when a template was successfully rendered.  The
   signal is invoked with the instance of the template as `template`
   and the context as dictionary (named `context`).

   Example subscriber::

        def log_template_renders(sender, template, context, **extra):
            sender.logger.debug('Rendering template "%s" with context %s',
                                template.name or 'string template',
                                context)

        from flask import template_rendered
        template_rendered.connect(log_template_renders, app)

.. data:: flask.before_render_template
   :noindex:

   This signal is sent before template rendering process. The
   signal is invoked with the instance of the template as `template`
   and the context as dictionary (named `context`).

   Example subscriber::

        def log_template_renders(sender, template, context, **extra):
            sender.logger.debug('Rendering template "%s" with context %s',
                                template.name or 'string template',
                                context)

        from flask import before_render_template
        before_render_template.connect(log_template_renders, app)

.. data:: request_started

   This signal is sent when the request context is set up, before
   any request processing happens.  Because the request context is already
   bound, the subscriber can access the request with the standard global
   proxies such as :class:`~flask.request`.

   Example subscriber::

        def log_request(sender, **extra):
            sender.logger.debug('Request context is set up')

        from flask import request_started
        request_started.connect(log_request, app)

.. data:: request_finished

   This signal is sent right before the response is sent to the client.
   It is passed the response to be sent named `response`.

   Example subscriber::

        def log_response(sender, response, **extra):
            sender.logger.debug('Request context is about to close down.  '
                                'Response: %s', response)

        from flask import request_finished
        request_finished.connect(log_response, app)

.. data:: got_request_exception

   This signal is sent when an exception happens during request processing.
   It is sent *before* the standard exception handling kicks in and even
   in debug mode, where no exception handling happens.  The exception
   itself is passed to the subscriber as `exception`.

   Example subscriber::

        def log_exception(sender, exception, **extra):
            sender.logger.debug('Got exception during processing: %s', exception)

        from flask import got_request_exception
        got_request_exception.connect(log_exception, app)

.. data:: request_tearing_down

   This signal is sent when the request is tearing down.  This is always
   called, even if an exception is caused.  Currently functions listening
   to this signal are called after the regular teardown handlers, but this
   is not something you can rely on.

   Example subscriber::

        def close_db_connection(sender, **extra):
            session.close()

        from flask import request_tearing_down
        request_tearing_down.connect(close_db_connection, app)

   As of Flask 0.9, this will also be passed an `exc` keyword argument
   that has a reference to the exception that caused the teardown if
   there was one.

.. data:: appcontext_tearing_down

   This signal is sent when the app context is tearing down.  This is always
   called, even if an exception is caused.  Currently functions listening
   to this signal are called after the regular teardown handlers, but this
   is not something you can rely on.

   Example subscriber::

        def close_db_connection(sender, **extra):
            session.close()

        from flask import appcontext_tearing_down
        appcontext_tearing_down.connect(close_db_connection, app)

   This will also be passed an `exc` keyword argument that has a reference
   to the exception that caused the teardown if there was one.

.. data:: appcontext_pushed

   This signal is sent when an application context is pushed.  The sender
   is the application.  This is usually useful for unittests in order to
   temporarily hook in information.  For instance it can be used to
   set a resource early onto the `g` object.

   Example usage::

        from contextlib import contextmanager
        from flask import appcontext_pushed

        @contextmanager
        def user_set(app, user):
            def handler(sender, **kwargs):
                g.user = user
            with appcontext_pushed.connected_to(handler, app):
                yield

   And in the testcode::

        def test_user_me(self):
            with user_set(app, 'john'):
                c = app.test_client()
                resp = c.get('/users/me')
                assert resp.data == 'username=john'

   .. versionadded:: 0.10

.. data:: appcontext_popped

   This signal is sent when an application context is popped.  The sender
   is the application.  This usually falls in line with the
   :data:`appcontext_tearing_down` signal.

   .. versionadded:: 0.10


.. data:: message_flashed

   This signal is sent when the application is flashing a message.  The
   messages is sent as `message` keyword argument and the category as
   `category`.

   Example subscriber::

        recorded = []
        def record(sender, message, category, **extra):
            recorded.append((message, category))

        from flask import message_flashed
        message_flashed.connect(record, app)

   .. versionadded:: 0.10

.. class:: signals.Namespace

   An alias for :class:`blinker.base.Namespace` if blinker is available,
   otherwise a dummy class that creates fake signals.  This class is
   available for Flask extensions that want to provide the same fallback
   system as Flask itself.

   .. method:: signal(name, doc=None)

      Creates a new signal for this namespace if blinker is available,
      otherwise returns a fake signal that has a send method that will
      do nothing but will fail with a :exc:`RuntimeError` for all other
      operations, including connecting.


.. _blinker: https://pypi.org/project/blinker/

.. _class-based-views:

Class-Based Views
-----------------

.. versionadded:: 0.7

.. currentmodule:: None

.. autoclass:: flask.views.View
   :members:

.. autoclass:: flask.views.MethodView
   :members:

.. _url-route-registrations:

URL Route Registrations
-----------------------

Generally there are three ways to define rules for the routing system:

1.  You can use the :meth:`flask.Flask.route` decorator.
2.  You can use the :meth:`flask.Flask.add_url_rule` function.
3.  You can directly access the underlying Werkzeug routing system
    which is exposed as :attr:`flask.Flask.url_map`.

Variable parts in the route can be specified with angular brackets
(``/user/<username>``).  By default a variable part in the URL accepts any
string without a slash however a different converter can be specified as
well by using ``<converter:name>``.

Variable parts are passed to the view function as keyword arguments.

The following converters are available:

=========== ===============================================
`string`    accepts any text without a slash (the default)
`int`       accepts integers
`float`     like `int` but for floating point values
`path`      like the default but also accepts slashes
`any`       matches one of the items provided
`uuid`      accepts UUID strings
=========== ===============================================

Custom converters can be defined using :attr:`flask.Flask.url_map`.

Here are some examples::

    @app.route('/')
    def index():
        pass

    @app.route('/<username>')
    def show_user(username):
        pass

    @app.route('/post/<int:post_id>')
    def show_post(post_id):
        pass

An important detail to keep in mind is how Flask deals with trailing
slashes.  The idea is to keep each URL unique so the following rules
apply:

1. If a rule ends with a slash and is requested without a slash by the
   user, the user is automatically redirected to the same page with a
   trailing slash attached.
2. If a rule does not end with a trailing slash and the user requests the
   page with a trailing slash, a 404 not found is raised.

This is consistent with how web servers deal with static files.  This
also makes it possible to use relative link targets safely.

You can also define multiple rules for the same function.  They have to be
unique however.  Defaults can also be specified.  Here for example is a
definition for a URL that accepts an optional page::

    @app.route('/users/', defaults={'page': 1})
    @app.route('/users/page/<int:page>')
    def show_users(page):
        pass

This specifies that ``/users/`` will be the URL for page one and
``/users/page/N`` will be the URL for page ``N``.

If a URL contains a default value, it will be redirected to its simpler
form with a 301 redirect. In the above example, ``/users/page/1`` will
be redirected to ``/users/``. If your route handles ``GET`` and ``POST``
requests, make sure the default route only handles ``GET``, as redirects
can't preserve form data. ::

   @app.route('/region/', defaults={'id': 1})
   @app.route('/region/<int:id>', methods=['GET', 'POST'])
   def region(id):
      pass

Here are the parameters that :meth:`~flask.Flask.route` and
:meth:`~flask.Flask.add_url_rule` accept.  The only difference is that
with the route parameter the view function is defined with the decorator
instead of the `view_func` parameter.

=============== ==========================================================
`rule`          the URL rule as string
`endpoint`      the endpoint for the registered URL rule.  Flask itself
                assumes that the name of the view function is the name
                of the endpoint if not explicitly stated.
`view_func`     the function to call when serving a request to the
                provided endpoint.  If this is not provided one can
                specify the function later by storing it in the
                :attr:`~flask.Flask.view_functions` dictionary with the
                endpoint as key.
`defaults`      A dictionary with defaults for this rule.  See the
                example above for how defaults work.
`subdomain`     specifies the rule for the subdomain in case subdomain
                matching is in use.  If not specified the default
                subdomain is assumed.
`**options`     the options to be forwarded to the underlying
                :class:`~werkzeug.routing.Rule` object.  A change to
                Werkzeug is handling of method options.  methods is a list
                of methods this rule should be limited to (``GET``, ``POST``
                etc.).  By default a rule just listens for ``GET`` (and
                implicitly ``HEAD``).  Starting with Flask 0.6, ``OPTIONS`` is
                implicitly added and handled by the standard request
                handling.  They have to be specified as keyword arguments.
=============== ==========================================================

.. _view-func-options:

View Function Options
---------------------

For internal usage the view functions can have some attributes attached to
customize behavior the view function would normally not have control over.
The following attributes can be provided optionally to either override
some defaults to :meth:`~flask.Flask.add_url_rule` or general behavior:

-   `__name__`: The name of a function is by default used as endpoint.  If
    endpoint is provided explicitly this value is used.  Additionally this
    will be prefixed with the name of the blueprint by default which
    cannot be customized from the function itself.

-   `methods`: If methods are not provided when the URL rule is added,
    Flask will look on the view function object itself if a `methods`
    attribute exists.  If it does, it will pull the information for the
    methods from there.

-   `provide_automatic_options`: if this attribute is set Flask will
    either force enable or disable the automatic implementation of the
    HTTP ``OPTIONS`` response.  This can be useful when working with
    decorators that want to customize the ``OPTIONS`` response on a per-view
    basis.

-   `required_methods`: if this attribute is set, Flask will always add
    these methods when registering a URL rule even if the methods were
    explicitly overridden in the ``route()`` call.

Full example::

    def index():
        if request.method == 'OPTIONS':
            # custom options handling here
            ...
        return 'Hello World!'
    index.provide_automatic_options = False
    index.methods = ['GET', 'OPTIONS']

    app.add_url_rule('/', index)

.. versionadded:: 0.8
   The `provide_automatic_options` functionality was added.

Command Line Interface
----------------------

.. currentmodule:: flask.cli

.. autoclass:: FlaskGroup
   :members:

.. autoclass:: AppGroup
   :members:

.. autoclass:: ScriptInfo
   :members:

.. autofunction:: load_dotenv

.. autofunction:: with_appcontext

.. autofunction:: pass_script_info

   Marks a function so that an instance of :class:`ScriptInfo` is passed
   as first argument to the click callback.

.. autodata:: run_command

.. autodata:: shell_command
