.. _api:

API
====

.. module:: flask

전체 문서 중 여기서는 플라스크의 모든 인터페이스를 다룬다. 플라스크에서
외부 라이브러리에 의존하는 부분에 대해서는 가장 중요한 것만 문서화했고
공식적인 문서에 대한 링크를 제공한다.


어플리케이션 객체(Application Object)
-------------------------------------------

.. autoclass:: Flask
   :members:
   :inherited-members:


블루프린트 객체(Blueprint Objects)
----------------------------------------

.. autoclass:: Blueprint
   :members:
   :inherited-members:

유입되는 요청 데이터(Incoming Request Data)
-------------------------------------------------

.. autoclass:: Request
   :members:

   .. attribute:: form

      `POST` 또는 `PUT` 요청으로 부터 파싱된 폼 데이터를 갖는 A :class:`~werkzeug.datastructures.MultiDict` .
      파일 업로드는 이 속성이 아닌 :attr:`files` 속성에서 처리되는 것을 명심해야한다.

   .. attribute:: args

      질의문의 파싱된 내용을 갖는 :class:`~werkzeug.datastructures.MultiDict` 
      (URL에서 물음표 뒤에 있는 부분).

   .. attribute:: values

      :attr:`form` 과 :attr:`args` 의 내용을 갖는 :class:`~werkzeug.datastructures.CombinedMultiDict` .

   .. attribute:: cookies

      요청과 같이 전송되는 모든 쿠키의 내용을 갖는 :class:`dict` .

   .. attribute:: stream

      유입되는 폼 데이터가 알려진 마임타입(MimeType)으로 인코딩되지 않았다면
      그 데이터는 변경되지 않은 상태로 이 스트림에 저장된다. 대부분의 경우
      문자로 이 데이터를 제공하는 :attr:`data` 를 사용하는게 나은 방식이다.
      스트림은 오직 한번 데이터를 반환한다.

   .. attribute:: headers

      딕셔너리 객체로 된 유입 요청 헤더.

   .. attribute:: data

      유입 요청 데이터가 플라스크가 다루지 않는 마임타입인 경우의 데이터.

   .. attribute:: files

      `POST` 또는 `PUT` 요청의 부분으로 파일 업로드를 갖는 :class:`~werkzeug.datastructures.MultiDict` .
      각 파일은 :class:`~werkzeug.datastructures.FileStorage` 객체로 저장된다.  기본적으로 파이썬에서 
      사용하는 표준 파일 객체처럼 동작하는데, 차이점은 이 객체는 파일 시스템에 파일을 저장할 수 있는
      :meth:`~werkzeug.datastructures.FileStorage.save` 함수가 있다.

   .. attribute:: environ

      기반이 되는 WSGI 환경.

   .. attribute:: method

      현재 요청에 대한 HTTP 메소드(``POST``, ``GET`` etc.)

   .. attribute:: path
   .. attribute:: script_root
   .. attribute:: url
   .. attribute:: base_url
   .. attribute:: url_root

      현재 URL을 바라보는 여러 방식을 제공한다.  아래와 같은 URL을 제공하는
      어플리케이션을 생각해보자::

          http://www.example.com/myapplication

      그리고 사용자는 아래와 같은 URL을 요청했다고 하자::

          http://www.example.com/myapplication/page.html?x=y

      이 경우 위에서 언급한 속성값은 아래와 같이 될 것이다:

      ============= ======================================================
      `path`        ``/page.html``
      `script_root` ``/myapplication``
      `base_url`    ``http://www.example.com/myapplication/page.html``
      `url`         ``http://www.example.com/myapplication/page.html?x=y``
      `url_root`    ``http://www.example.com/myapplication/``
      ============= ======================================================

   .. attribute:: is_xhr

      요청이 자바스크립트 `XMLHttpRequest` 으로 요청됐다면 `True` .
      이 속성은 ``X-Requested-With`` 헤더를 지원하고 `XMLHttpRequest` 에
      그것을 설정하는 라이브러리와만 동작한다. prototype, jQuery 그리고
      Mochikit 등이 그런 라이브러리다.

.. class:: request

   유입 요청 데이터에 접근하기 위해서, 여러분은 전역 `request` 객체를 사용할 수 있다.
   플라스크는 유입 요청 데이터를 파싱해서 전역 객체로 그 데이터에 접근하게 해준다.
   내부적으로 플라스크는 여러분이 다중 쓰레드 환경에 있더라도 활성화된 요청 쓰레드에
   대해 올바른 데이터를 얻는 것을 보장한다.

   이것은 일종의 프록시다.  더 많은 정보는 :ref:`notes-on-proxies` 를 살펴봐라.

   이 요청 객체는 :class:`~werkzeug.wrappers.Request` 하위 클래스의 인스턴스이고 벡자이크가
   정의한 모든 속성을 제공한다.  이 객체는 가장 중요한 객체에 대한 빠른 개요를 보여준다.


응답 객체(Response Objects)
--------------------------------

.. autoclass:: flask.Response
   :members: set_cookie, data, mimetype

   .. attribute:: headers

      응답 헤더를 나타내는 :class:`Headers` 객체.

   .. attribute:: status

      응답 상태를 갖는 문자열.

   .. attribute:: status_code

      정수형의 응답 상태코드.


세션(Sessions)
-----------------

여러분이 :attr:`Flask.secret_key` 속성을 설정한다면 플라스크 어플리케이션에
있는 세션을 사용할 수 있다.  세션은 기본적으로 하나의 요청 정보를 다른 요청에서
기억하게 해준다.  플라스크에서는 서명된 쿠기(singed cookie)를 이용한다.  
그래서 사용자가 세션 내용을 볼 수는 있으나 비밀키를 모른다면 그 내용을 수정할
수 없기 때문에 그 키를 복잡하고 추측할 수 없게 설정해도록 해야한다.

현재 세션에 접근하기 위해서 :class:`session` 객체를 사용한다:

.. class:: session

   세션 객체는 보통 딕셔너리 객체와 상당히 비슷하게 동작하는데
   차이점은 수정사항을 유지한다는 것이다.
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
----------------------

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
---------------

.. currentmodule:: flask.testing

.. autoclass:: FlaskClient
   :members:


Application Globals
------------------------

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
-----------------------------------

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
--------------------

.. autofunction:: flash

.. autofunction:: get_flashed_messages

JSON Support
---------------

.. module:: flask.json

Flask uses ``simplejson`` for the JSON implementation.  Since simplejson
is provided both by the standard library as well as extension Flask will
try simplejson first and then fall back to the stdlib json module.  On top
of that it will delegate access to the current application's JSOn encoders
and decoders for easier customization.

So for starters instead of doing::

    try:
        import simplejson as json
    except ImportError:
        import json

You can instead just do this::

    from flask import json

For usage examples, read the :mod:`json` documentation in the standard
lirbary.  The following extensions are by default applied to the stdlib's
JSON module:

1.  ``datetime`` objects are serialized as :rfc:`822` strings.
2.  Any object with an ``__html__`` method (like :class:`~flask.Markup`)
    will ahve that method called and then the return value is serialized
    as string.

The :func:`~htmlsafe_dumps` function of this json module is also available
as filter called ``|tojson`` in Jinja2.  Note that inside `script`
tags no escaping must take place, so make sure to disable escaping
with ``|safe`` if you intend to use it inside `script` tags:

.. sourcecode:: html+jinja

    <script type=text/javascript>
        doSomethingWith({{ user.username|tojson|safe }});
    </script>

Note that the ``|tojson`` filter escapes forward slashes properly.

.. autofunction:: jsonify

.. autofunction:: dumps

.. autofunction:: dump

.. autofunction:: loads

.. autofunction:: load

.. autoclass:: JSONEncoder
   :members:

.. autoclass:: JSONDecoder
   :members:

Template Rendering
----------------------

.. currentmodule:: flask

.. autofunction:: render_template

.. autofunction:: render_template_string

.. autofunction:: get_template_attribute

Configuration
----------------

.. autoclass:: Config
   :members:

Extensions
-------------

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
-----------------

.. autofunction:: stream_with_context

Useful Internals
-------------------

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
---------

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
---------------------

.. versionadded:: 0.7

.. currentmodule:: None

.. autoclass:: flask.views.View
   :members:

.. autoclass:: flask.views.MethodView
   :members:

.. _url-route-registrations:

URL Route Registrations
----------------------------

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
-------------------------

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
