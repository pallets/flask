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

   .. attribute:: form

      A :class:`~werkzeug.datastructures.MultiDict` with the parsed form data from `POST`
      or `PUT` requests.  Please keep in mind that file uploads will not
      end up here,  but instead in the :attr:`files` attribute.

   .. attribute:: args

      A :class:`~werkzeug.datastructures.MultiDict` with the parsed contents of the query
      string.  (The part in the URL after the question mark).

   .. attribute:: values

      A :class:`~werkzeug.datastructures.CombinedMultiDict` with the contents of both
      :attr:`form` and :attr:`args`.

   .. attribute:: cookies

      A :class:`dict` with the contents of all cookies transmitted with
      the request.

   .. attribute:: stream

      If the incoming form data was not encoded with a known mimetype
      the data is stored unmodified in this stream for consumption.  Most
      of the time it is a better idea to use :attr:`data` which will give
      you that data as a string.  The stream only returns the data once.

   .. attribute:: headers

      The incoming request headers as a dictionary like object.

   .. attribute:: data

      Contains the incoming request data as string in case it came with
      a mimetype Flask does not handle.

   .. attribute:: files

      A :class:`~werkzeug.datastructures.MultiDict` with files uploaded as part of a
      `POST` or `PUT` request.  Each file is stored as
      :class:`~werkzeug.datastructures.FileStorage` object.  It basically behaves like a
      standard file object you know from Python, with the difference that
      it also has a :meth:`~werkzeug.datastructures.FileStorage.save` function that can
      store the file on the filesystem.

   .. attribute:: environ

      The underlying WSGI environment.

   .. attribute:: method

      The current request method (``POST``, ``GET`` etc.)

   .. attribute:: path
   .. attribute:: script_root
   .. attribute:: url
   .. attribute:: base_url
   .. attribute:: url_root

      Provides different ways to look at the current URL.  Imagine your
      application is listening on the following URL::

          http://www.example.com/myapplication

      And a user requests the following URL::

          http://www.example.com/myapplication/page.html?x=y

      In this case the values of the above mentioned attributes would be
      the following:

      ============= ======================================================
      `path`        ``/page.html``
      `script_root` ``/myapplication``
      `base_url`    ``http://www.example.com/myapplication/page.html``
      `url`         ``http://www.example.com/myapplication/page.html?x=y``
      `url_root`    ``http://www.example.com/myapplication/``
      ============= ======================================================

   .. attribute:: is_xhr

      `True` if the request was triggered via a JavaScript
      `XMLHttpRequest`. This only works with libraries that support the
      ``X-Requested-With`` header and set it to `XMLHttpRequest`.
      Libraries that do that are prototype, jQuery and Mochikit and
      probably some more.

.. class:: request

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
   :members: set_cookie, data, mimetype

   .. attribute:: headers

      A :class:`Headers` object representing the response headers.

   .. attribute:: status

      A string with a response status.

   .. attribute:: status_code

      The response status as integer.


Sessions
--------

If you have the :attr:`Flask.secret_key` set you can use sessions in Flask
applications.  A session basically makes it possible to remember
information from one request to another.  The way Flask does this is by
using a signed cookie.  So the user can look at the session contents, but
not modify it unless they know the secret key, so make sure to set that
to something complex and unguessable.

To access the current session you can use the :class:`session` object:

.. class:: session

   The session object works pretty much like an ordinary dict, with the
   difference that it keeps track on modifications.

   This is a proxy.  See :ref:`notes-on-proxies` for more information.

   The following attributes are interesting:

   .. attribute:: new

      `True` if the session is new, `False` otherwise.

   .. attribute:: modified

      `True` if the session object detected a modification.  Be advised
      that modifications on mutable structures are not picked up
      automatically, in that situation you have to explicitly set the
      attribute to `True` yourself.  Here an example::

          # this change is not picked up because a mutable object (here
          # a list) is changed.
          session['objects'].append(42)
          # so mark it as modified yourself
          session.modified = True

   .. attribute:: permanent

      If set to `True` the session lives for
      :attr:`~flask.Flask.permanent_session_lifetime` seconds.  The
      default is 31 days.  If set to `False` (which is the default) the
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

   Just store on this whatever you want.  For example a database
   connection or the user that is currently logged in.

   This is a proxy.  See :ref:`notes-on-proxies` for more information.


Useful Functions and Classes
----------------------------

.. data:: current_app

   Points to the application handling the request.  This is useful for
   extensions that want to support multiple applications running side
   by side.  This is powered by the application context and not by the
   request context, so you can change the value of this proxy by
   using the :meth:`~flask.Flask.app_context` method.

   This is a proxy.  See :ref:`notes-on-proxies` for more information.

.. autofunction:: has_request_context

.. autofunction:: has_app_context

.. autofunction:: url_for

.. function:: abort(code)

   Raises an :exc:`~werkzeug.exceptions.HTTPException` for the given
   status code.  For example to abort request handling with a page not
   found exception, you would call ``abort(404)``.

   :param code: the HTTP error code.

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

Returning JSON
--------------

.. autofunction:: jsonify

.. data:: json

    If JSON support is picked up, this will be the module that Flask is
    using to parse and serialize JSON.  So instead of doing this yourself::

        try:
            import simplejson as json
        except ImportError:
            import json

    You can instead just do this::

        from flask import json

    For usage examples, read the :mod:`json` documentation.

    The :func:`~json.dumps` function of this json module is also available
    as filter called ``|tojson`` in Jinja2.  Note that inside `script`
    tags no escaping must take place, so make sure to disable escaping
    with ``|safe`` if you intend to use it inside `script` tags:

    .. sourcecode:: html+jinja

        <script type=text/javascript>
            doSomethingWith({{ user.username|tojson|safe }});
        </script>

    Note that the ``|tojson`` filter escapes forward slashes properly.

Template Rendering
------------------

.. autofunction:: render_template

.. autofunction:: render_template_string

.. autofunction:: get_template_attribute

Configuration
-------------

.. autoclass:: Config
   :members:

Extensions
----------

.. data:: flask.ext

   This module acts as redirect import module to Flask extensions.  It was
   added in 0.8 as the canonical way to import Flask extensions and makes
   it possible for us to have more flexibility in how we distribute
   extensions.

   If you want to use an extension named “Flask-Foo” you would import it
   from :data:`~flask.ext` as follows::

        from flask.ext import foo

   .. versionadded:: 0.8

Stream Helpers
--------------

.. autofunction:: stream_with_context

Useful Internals
----------------

.. autoclass:: flask.ctx.RequestContext
   :members:

.. data:: _request_ctx_stack

   The internal :class:`~werkzeug.local.LocalStack` that is used to implement
   all the context local objects used in Flask.  This is a documented
   instance and can be used by extensions and application code but the
   use is discouraged in general.

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

   Works similar to the request context but only binds the application.
   This is mainly there for extensions to store data.

   .. versionadded:: 0.9

.. autoclass:: flask.blueprints.BlueprintSetupState
   :members:

Signals
-------

.. when modifying this list, also update the one in signals.rst

.. versionadded:: 0.6

.. data:: signals_available

   `True` if the signalling system is available.  This is the case
   when `blinker`_ is installed.

.. data:: template_rendered

   This signal is sent when a template was successfully rendered.  The
   signal is invoked with the instance of the template as `template`
   and the context as dictionary (named `context`).

.. data:: request_started

   This signal is sent before any request processing started but when the
   request context was set up.  Because the request context is already
   bound, the subscriber can access the request with the standard global
   proxies such as :class:`~flask.request`.

.. data:: request_finished

   This signal is sent right before the response is sent to the client.
   It is passed the response to be sent named `response`.

.. data:: got_request_exception

   This signal is sent when an exception happens during request processing.
   It is sent *before* the standard exception handling kicks in and even
   in debug mode, where no exception handling happens.  The exception
   itself is passed to the subscriber as `exception`.

.. data:: request_tearing_down

   This signal is sent when the application is tearing down the request.
   This is always called, even if an error happened.  An `exc` keyword
   argument is passed with the exception that caused the teardown.

   .. versionchanged:: 0.9
      The `exc` parameter was added.

.. data:: appcontext_tearing_down

   This signal is sent when the application is tearing down the
   application context.  This is always called, even if an error happened.
   An `exc` keyword argument is passed with the exception that caused the
   teardown.

.. currentmodule:: None

.. class:: flask.signals.Namespace

   An alias for :class:`blinker.base.Namespace` if blinker is available,
   otherwise a dummy class that creates fake signals.  This class is
   available for Flask extensions that want to provide the same fallback
   system as Flask itself.

   .. method:: signal(name, doc=None)

      Creates a new signal for this namespace if blinker is available,
      otherwise returns a fake signal that has a send method that will
      do nothing but will fail with a :exc:`RuntimeError` for all other
      operations, including connecting.

.. _blinker: http://pypi.python.org/pypi/blinker

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
=========== ===============================================

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
``/users/page/N`` will be the URL for page `N`.

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
                of methods this rule should be limited to (`GET`, `POST`
                etc.).  By default a rule just listens for `GET` (and
                implicitly `HEAD`).  Starting with Flask 0.6, `OPTIONS` is
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
    Flask will look on the view function object itself is an `methods`
    attribute exists.  If it does, it will pull the information for the
    methods from there.

-   `provide_automatic_options`: if this attribute is set Flask will
    either force enable or disable the automatic implementation of the
    HTTP `OPTIONS` response.  This can be useful when working with
    decorators that want to customize the `OPTIONS` response on a per-view
    basis.

-   `required_methods`: if this attribute is set, Flask will always add
    these methods when registering a URL rule even if the methods were
    explicitly overriden in the ``route()`` call.

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
