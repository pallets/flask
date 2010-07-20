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


Module Objects
--------------

.. autoclass:: Module
   :members:
   :inherited-members:

Incoming Request Data
---------------------

.. autoclass:: Request

.. class:: request

   To access incoming request data, you can use the global `request`
   object.  Flask parses incoming request data for you and gives you
   access to it through that global object.  Internally Flask makes
   sure that you always get the correct data for the active thread if you
   are in a multithreaded environment.

   This is a proxy.  See :ref:`notes-on-proxies` for more information.

   The request object is an instance of a :class:`~werkzeug.Request`
   subclass and provides all of the attributes Werkzeug defines.  This
   just shows a quick overview of the most important ones.

   .. attribute:: form

      A :class:`~werkzeug.MultiDict` with the parsed form data from `POST`
      or `PUT` requests.  Please keep in mind that file uploads will not
      end up here,  but instead in the :attr:`files` attribute.

   .. attribute:: args

      A :class:`~werkzeug.MultiDict` with the parsed contents of the query
      string.  (The part in the URL after the question mark).

   .. attribute:: values

      A :class:`~werkzeug.CombinedMultiDict` with the contents of both
      :attr:`form` and :attr:`args`.

   .. attribute:: cookies

      A :class:`dict` with the contents of all cookies transmitted with
      the request.

   .. attribute:: stream

      If the incoming form data was not encoded with a known mimetype
      the data is stored unmodified in this stream for consumption.  Most
      of the time it is a better idea to use :attr:`data` which will give
      you that data as a string.  The stream only returns the data once.

   .. attribute:: data

      Contains the incoming request data as string in case it came with
      a mimetype Flask does not handle.

   .. attribute:: files

      A :class:`~werkzeug.MultiDict` with files uploaded as part of a
      `POST` or `PUT` request.  Each file is stored as
      :class:`~werkzeug.FileStorage` object.  It basically behaves like a
      standard file object you know from Python, with the difference that
      it also has a :meth:`~werkzeug.FileStorage.save` function that can
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

   .. attribute:: json

      Contains the parsed body of the JSON request if the mimetype of
      the incoming data was `application/json`.  This requires Python 2.6
      or an installed version of simplejson.

Response Objects
----------------

.. autoclass:: flask.Response
   :members: set_cookie, data, mimetype

   .. attribute:: headers

      A :class:`Headers` object representing the response headers.

   .. attribute:: status_code

      The response status as integer.


Sessions
--------

If you have the :attr:`Flask.secret_key` set you can use sessions in Flask
applications.  A session basically makes it possible to remember
information from one request to another.  The way Flask does this is by
using a signed cookie.  So the user can look at the session contents, but
not modify it unless he knows the secret key, so make sure to set that to
something complex and unguessable.

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

       If set to `True` the session life for
       :attr:`~flask.Flask.permanent_session_lifetime` seconds.  The
       default is 31 days.  If set to `False` (which is the default) the
       session will be deleted when the user closes the browser.


Application Globals
-------------------

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
   by side.

   This is a proxy.  See :ref:`notes-on-proxies` for more information.

.. autofunction:: url_for

.. function:: abort(code)

   Raises an :exc:`~werkzeug.exception.HTTPException` for the given
   status code.  For example to abort request handling with a page not
   found exception, you would call ``abort(404)``.

   :param code: the HTTP error code.

.. autofunction:: redirect

.. autofunction:: make_response

.. autofunction:: send_file

.. autofunction:: send_from_directory

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

Useful Internals
----------------

.. data:: _request_ctx_stack

   The internal :class:`~werkzeug.LocalStack` that is used to implement
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

   .. versionchanged:: 0.4

   The request context is automatically popped at the end of the request
   for you.  In debug mode the request context is kept around if
   exceptions happen so that interactive debuggers have a chance to
   introspect the data.  With 0.4 this can also be forced for requests
   that did not fail and outside of `DEBUG` mode.  By setting
   ``'flask._preserve_context'`` to `True` on the WSGI environment the
   context will not pop itself at the end of the request.  This is used by
   the :meth:`~flask.Flask.test_client` for example to implement the
   deferred cleanup functionality.

   You might find this helpful for unittests where you need the
   information from the context local around for a little longer.  Make
   sure to properly :meth:`~werkzeug.LocalStack.pop` the stack yourself in
   that situation, otherwise your unittests will leak memory.

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

.. _notes-on-proxies:

Notes On Proxies
----------------

Some of the objects provided by Flask are proxies to other objects.  The
reason behind this is, that these proxies are shared between threads and
they have to dispatch to the actual object bound to a thread behind the
scenes as necessary.

Most of the time you don't have to care about that, but there are some
exceptions where it is good to know that this object is an actual proxy:

-   The proxy objects do not fake their inherited types, so if you want to
    perform actual instance checks, you have to do that on the instance
    that
-   if the object reference is important (so for example for sending
    :ref:`signals`)

If you need to get access to the underlying object that is proxied, you
can use the :meth:`~werkzeug.LocalProxy._get_current_object` method::

    app = current_app._get_current_object()
    my_signal.send(app)
