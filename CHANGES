Flask Changelog
===============

Here you can see the full list of changes between each Flask release.

Version 0.9
-----------

Released on July 1st 2012, codename Camapri.

- The :func:`flask.Request.on_json_loading_failed` now returns a JSON formatted
  response by default.
- The :func:`flask.url_for` function now can generate anchors to the
  generated links.
- The :func:`flask.url_for` function now can also explicitly generate
  URL rules specific to a given HTTP method.
- Logger now only returns the debug log setting if it was not set
  explicitly.
- Unregister a circular dependency between the WSGI environment and
  the request object when shutting down the request.  This means that
  environ ``werkzeug.request`` will be `None` after the response was
  returned to the WSGI server but has the advantage that the garbage
  collector is not needed on CPython to tear down the request unless
  the user created circular dependencies themselves.
- Session is now stored after callbacks so that if the session payload
  is stored in the session you can still modify it in an after
  request callback.
- The :class:`flask.Flask` class will avoid importing the provided import name
  if it can (the required first parameter), to benefit tools which build Flask
  instances programmatically.  The Flask class will fall back to using import
  on systems with custom module hooks, e.g. Google App Engine, or when the
  import name is inside a zip archive (usually a .egg) prior to Python 2.7.
- Blueprints now have a decorator to add custom template filters application
  wide, :meth:`flask.Blueprint.app_template_filter`.
- The Flask and Blueprint classes now have a non-decorator method for adding
  custom template filters application wide,
  :meth:`flask.Flask.add_template_filter` and
  :meth:`flask.Blueprint.add_app_template_filter`.
- The :func:`flask.get_flashed_messages` function now allows rendering flashed
  message categories in separate blocks, through a ``category_filter``
  argument.
- The :meth:`flask.Flask.run` method now accepts `None` for `host` and `port`
  arguments, using default values when `None`.  This allows for calling run
  using configuration values, e.g. ``app.run(app.config.get('MYHOST'),
  app.config.get('MYPORT'))``, with proper behavior whether or not a config
  file is provided.
- The :meth:`flask.render_template` method now accepts a either an iterable of
  template names or a single template name.  Previously, it only accepted a
  single template name.  On an iterable, the first template found is rendered.
- Added :meth:`flask.Flask.app_context` which works very similar to the
  request context but only provides access to the current application.  This
  also adds support for URL generation without an active request context.
- View functions can now return a tuple with the first instance being an
  instance of :class:`flask.Response`.  This allows for returning
  ``jsonify(error="error msg"), 400`` from a view function.
- :class:`~flask.Flask` and :class:`~flask.Blueprint` now provide a
  :meth:`~flask.Flask.get_send_file_max_age` hook for subclasses to override
  behavior of serving static files from Flask when using
  :meth:`flask.Flask.send_static_file` (used for the default static file
  handler) and :func:`~flask.helpers.send_file`.  This hook is provided a
  filename, which for example allows changing cache controls by file extension.
  The default max-age for `send_file` and static files can be configured
  through a new ``SEND_FILE_MAX_AGE_DEFAULT`` configuration variable, which is
  used in the default `get_send_file_max_age` implementation.
- Fixed an assumption in sessions implementation which could break message
  flashing on sessions implementations which use external storage.
- Changed the behavior of tuple return values from functions.  They are no
  longer arguments to the response object, they now have a defined meaning.
- Added :attr:`flask.Flask.request_globals_class` to allow a specific class to
  be used on creation of the :data:`~flask.g` instance of each request.
- Added `required_methods` attribute to view functions to force-add methods
  on registration.
- Added :func:`flask.after_this_request`.
- Added :func:`flask.stream_with_context` and the ability to push contexts
  multiple times without producing unexpected behavior.

Version 0.8.1
-------------

Bugfix release, released on July 1th 2012

- Fixed an issue with the undocumented `flask.session` module to not
  work properly on Python 2.5.  It should not be used but did cause
  some problems for package managers.

Version 0.8
-----------

Released on September 29th 2011, codename Rakija

- Refactored session support into a session interface so that
  the implementation of the sessions can be changed without
  having to override the Flask class.
- Empty session cookies are now deleted properly automatically.
- View functions can now opt out of getting the automatic
  OPTIONS implementation.
- HTTP exceptions and Bad Request errors can now be trapped so that they
  show up normally in the traceback.
- Flask in debug mode is now detecting some common problems and tries to
  warn you about them.
- Flask in debug mode will now complain with an assertion error if a view
  was attached after the first request was handled.  This gives earlier
  feedback when users forget to import view code ahead of time.
- Added the ability to register callbacks that are only triggered once at
  the beginning of the first request. (:meth:`Flask.before_first_request`)
- Malformed JSON data will now trigger a bad request HTTP exception instead
  of a value error which usually would result in a 500 internal server
  error if not handled.  This is a backwards incompatible change.
- Applications now not only have a root path where the resources and modules
  are located but also an instance path which is the designated place to
  drop files that are modified at runtime (uploads etc.).  Also this is
  conceptionally only instance depending and outside version control so it's
  the perfect place to put configuration files etc.  For more information
  see :ref:`instance-folders`.
- Added the ``APPLICATION_ROOT`` configuration variable.
- Implemented :meth:`~flask.testing.TestClient.session_transaction` to
  easily modify sessions from the test environment.
- Refactored test client internally.  The ``APPLICATION_ROOT`` configuration
  variable as well as ``SERVER_NAME`` are now properly used by the test client
  as defaults.
- Added :attr:`flask.views.View.decorators` to support simpler decorating of
  pluggable (class-based) views.
- Fixed an issue where the test client if used with the "with" statement did not
  trigger the execution of the teardown handlers.
- Added finer control over the session cookie parameters.
- HEAD requests to a method view now automatically dispatch to the `get`
  method if no handler was implemented.
- Implemented the virtual :mod:`flask.ext` package to import extensions from.
- The context preservation on exceptions is now an integral component of
  Flask itself and no longer of the test client.  This cleaned up some
  internal logic and lowers the odds of runaway request contexts in unittests.

Version 0.7.3
-------------

Bugfix release, release date to be decided

- Fixed the Jinja2 environment's list_templates method not returning the
  correct names when blueprints or modules were involved.

Version 0.7.2
-------------

Bugfix release, released on July 6th 2011

- Fixed an issue with URL processors not properly working on
  blueprints.

Version 0.7.1
-------------

Bugfix release, released on June 29th 2011

- Added missing future import that broke 2.5 compatibility.
- Fixed an infinite redirect issue with blueprints.

Version 0.7
-----------

Released on June 28th 2011, codename Grappa

- Added :meth:`~flask.Flask.make_default_options_response`
  which can be used by subclasses to alter the default
  behavior for `OPTIONS` responses.
- Unbound locals now raise a proper :exc:`RuntimeError` instead
  of an :exc:`AttributeError`.
- Mimetype guessing and etag support based on file objects is now
  deprecated for :func:`flask.send_file` because it was unreliable.
  Pass filenames instead or attach your own etags and provide a
  proper mimetype by hand.
- Static file handling for modules now requires the name of the
  static folder to be supplied explicitly.  The previous autodetection
  was not reliable and caused issues on Google's App Engine.  Until
  1.0 the old behavior will continue to work but issue dependency
  warnings.
- fixed a problem for Flask to run on jython.
- added a `PROPAGATE_EXCEPTIONS` configuration variable that can be
  used to flip the setting of exception propagation which previously
  was linked to `DEBUG` alone and is now linked to either `DEBUG` or
  `TESTING`.
- Flask no longer internally depends on rules being added through the
  `add_url_rule` function and can now also accept regular werkzeug
  rules added to the url map.
- Added an `endpoint` method to the flask application object which
  allows one to register a callback to an arbitrary endpoint with
  a decorator.
- Use Last-Modified for static file sending instead of Date which
  was incorrectly introduced in 0.6.
- Added `create_jinja_loader` to override the loader creation process.
- Implemented a silent flag for `config.from_pyfile`.
- Added `teardown_request` decorator, for functions that should run at the end
  of a request regardless of whether an exception occurred.  Also the behavior
  for `after_request` was changed.  It's now no longer executed when an exception
  is raised.  See :ref:`upgrading-to-new-teardown-handling`
- Implemented :func:`flask.has_request_context`
- Deprecated `init_jinja_globals`.  Override the
  :meth:`~flask.Flask.create_jinja_environment` method instead to
  achieve the same functionality.
- Added :func:`flask.safe_join`
- The automatic JSON request data unpacking now looks at the charset
  mimetype parameter.
- Don't modify the session on :func:`flask.get_flashed_messages` if there
  are no messages in the session.
- `before_request` handlers are now able to abort requests with errors.
- it is not possible to define user exception handlers.  That way you can
  provide custom error messages from a central hub for certain errors that
  might occur during request processing (for instance database connection
  errors, timeouts from remote resources etc.).
- Blueprints can provide blueprint specific error handlers.
- Implemented generic :ref:`views` (class-based views).

Version 0.6.1
-------------

Bugfix release, released on December 31st 2010

- Fixed an issue where the default `OPTIONS` response was
  not exposing all valid methods in the `Allow` header.
- Jinja2 template loading syntax now allows "./" in front of
  a template load path.  Previously this caused issues with
  module setups.
- Fixed an issue where the subdomain setting for modules was
  ignored for the static folder.
- Fixed a security problem that allowed clients to download arbitrary files
  if the host server was a windows based operating system and the client
  uses backslashes to escape the directory the files where exposed from.

Version 0.6
-----------

Released on July 27th 2010, codename Whisky

- after request functions are now called in reverse order of
  registration.
- OPTIONS is now automatically implemented by Flask unless the
  application explicitly adds 'OPTIONS' as method to the URL rule.
  In this case no automatic OPTIONS handling kicks in.
- static rules are now even in place if there is no static folder
  for the module.  This was implemented to aid GAE which will
  remove the static folder if it's part of a mapping in the .yml
  file.
- the :attr:`~flask.Flask.config` is now available in the templates
  as `config`.
- context processors will no longer override values passed directly
  to the render function.
- added the ability to limit the incoming request data with the
  new ``MAX_CONTENT_LENGTH`` configuration value.
- the endpoint for the :meth:`flask.Module.add_url_rule` method
  is now optional to be consistent with the function of the
  same name on the application object.
- added a :func:`flask.make_response` function that simplifies
  creating response object instances in views.
- added signalling support based on blinker.  This feature is currently
  optional and supposed to be used by extensions and applications.  If
  you want to use it, make sure to have `blinker`_ installed.
- refactored the way URL adapters are created.  This process is now
  fully customizable with the :meth:`~flask.Flask.create_url_adapter`
  method.
- modules can now register for a subdomain instead of just an URL
  prefix.  This makes it possible to bind a whole module to a
  configurable subdomain.

.. _blinker: http://pypi.python.org/pypi/blinker

Version 0.5.2
-------------

Bugfix Release, released on July 15th 2010

- fixed another issue with loading templates from directories when
  modules were used.

Version 0.5.1
-------------

Bugfix Release, released on July 6th 2010

- fixes an issue with template loading from directories when modules
  where used.

Version 0.5
-----------

Released on July 6th 2010, codename Calvados

- fixed a bug with subdomains that was caused by the inability to
  specify the server name.  The server name can now be set with
  the `SERVER_NAME` config key.  This key is now also used to set
  the session cookie cross-subdomain wide.
- autoescaping is no longer active for all templates.  Instead it
  is only active for ``.html``, ``.htm``, ``.xml`` and ``.xhtml``.
  Inside templates this behavior can be changed with the
  ``autoescape`` tag.
- refactored Flask internally.  It now consists of more than a
  single file.
- :func:`flask.send_file` now emits etags and has the ability to
  do conditional responses builtin.
- (temporarily) dropped support for zipped applications.  This was a
  rarely used feature and led to some confusing behavior.
- added support for per-package template and static-file directories.
- removed support for `create_jinja_loader` which is no longer used
  in 0.5 due to the improved module support.
- added a helper function to expose files from any directory.

Version 0.4
-----------

Released on June 18th 2010, codename Rakia

- added the ability to register application wide error handlers
  from modules.
- :meth:`~flask.Flask.after_request` handlers are now also invoked
  if the request dies with an exception and an error handling page
  kicks in.
- test client has not the ability to preserve the request context
  for a little longer.  This can also be used to trigger custom
  requests that do not pop the request stack for testing.
- because the Python standard library caches loggers, the name of
  the logger is configurable now to better support unittests.
- added `TESTING` switch that can activate unittesting helpers.
- the logger switches to `DEBUG` mode now if debug is enabled.

Version 0.3.1
-------------

Bugfix release, released on May 28th 2010

- fixed a error reporting bug with :meth:`flask.Config.from_envvar`
- removed some unused code from flask
- release does no longer include development leftover files (.git
  folder for themes, built documentation in zip and pdf file and
  some .pyc files)

Version 0.3
-----------

Released on May 28th 2010, codename Schnaps

- added support for categories for flashed messages.
- the application now configures a :class:`logging.Handler` and will
  log request handling exceptions to that logger when not in debug
  mode.  This makes it possible to receive mails on server errors
  for example.
- added support for context binding that does not require the use of
  the with statement for playing in the console.
- the request context is now available within the with statement making
  it possible to further push the request context or pop it.
- added support for configurations.

Version 0.2
-----------

Released on May 12th 2010, codename Jägermeister

- various bugfixes
- integrated JSON support
- added :func:`~flask.get_template_attribute` helper function.
- :meth:`~flask.Flask.add_url_rule` can now also register a
  view function.
- refactored internal request dispatching.
- server listens on 127.0.0.1 by default now to fix issues with chrome.
- added external URL support.
- added support for :func:`~flask.send_file`
- module support and internal request handling refactoring
  to better support pluggable applications.
- sessions can be set to be permanent now on a per-session basis.
- better error reporting on missing secret keys.
- added support for Google Appengine.

Version 0.1
-----------

First public preview release.
