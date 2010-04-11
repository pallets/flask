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

Incoming Request Data
---------------------

.. autoclass:: Request

.. class:: request

   To access incoming request data, you can use the global `request`
   object.  Flask parses incoming request data for you and gives you
   access to it through that global object.  Internally Flask makes
   sure that you always get the correct data for the active thread if you
   are in a multithreaded environment.

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

      If the incoming form data was not encoded with a known encoding (for
      example it was transmitted as JSON) the data is stored unmodified in
      this stream for consumption.  For example to read the incoming
      request data as JSON, one can do the following::

          json_body = simplejson.load(request.stream)

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
      `url`         ``http://www.example.com/myapplication/page.html``
      `base_url`    ``http://www.example.com/myapplication/page.html?x=y``
      `root_url`    ``http://www.example.com/myapplication/``
      ============= ======================================================

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


Useful Functions and Classes
----------------------------

.. autofunction:: url_for

.. function:: abort(code)

   Raises an :exc:`~werkzeug.exception.HTTPException` for the given
   status code.  For example to abort request handling with a page not
   found exception, you would call ``abort(404)``.

   :param code: the HTTP error code.

.. autofunction:: redirect

.. autofunction:: escape

.. autoclass:: Markup
   :members: escape, unescape, striptags

Message Flashing
----------------

.. autofunction:: flash

.. autofunction:: get_flashed_messages

Template Rendering
------------------

.. autofunction:: render_template

.. autofunction:: render_template_string
