.. _application-errors:

Application Errors
==================

.. versionadded:: 0.3

Applications fail, servers fail.  Sooner or later you will see an exception
in production.  Even if your code is 100% correct, you will still see
exceptions from time to time.  Why?  Because everything else involved will
fail.  Here are some situations where perfectly fine code can lead to server
errors:

-   the client terminated the request early and the application was still
    reading from the incoming data
-   the database server was overloaded and could not handle the query
-   a filesystem is full
-   a harddrive crashed
-   a backend server overloaded
-   a programming error in a library you are using
-   network connection of the server to another system failed

And that's just a small sample of issues you could be facing.  So how do we
deal with that sort of problem?  By default if your application runs in
production mode, Flask will display a very simple page for you and log the
exception to the :attr:`~flask.Flask.logger`.

But there is more you can do, and we will cover some better setups to deal
with errors.

Error Logging Tools
-------------------

Sending error mails, even if just for critical ones, can become
overwhelming if enough users are hitting the error and log files are
typically never looked at. This is why we recommend using `Sentry
<http://www.getsentry.com/>`_ for dealing with application errors.  It's
available as an Open Source project `on GitHub
<https://github.com/getsentry/sentry>`__ and is also available as a `hosted version
<https://getsentry.com/signup/>`_ which you can try for free. Sentry
aggregates duplicate errors, captures the full stack trace and local
variables for debugging, and sends you mails based on new errors or
frequency thresholds.

To use Sentry you need to install the `raven` client::

    $ pip install raven

And then add this to your Flask app::

    from raven.contrib.flask import Sentry
    sentry = Sentry(app, dsn='YOUR_DSN_HERE')

Of if you are using factories you can also init it later::

    from raven.contrib.flask import Sentry
    sentry = Sentry(dsn='YOUR_DSN_HERE')

    def create_app():
        app = Flask(__name__)
        sentry.init_app(app)
        ...
        return app

The `YOUR_DSN_HERE` value needs to be replaced with the DSN value you get
from your Sentry installation.

Afterwards failures are automatically reported to Sentry and from there
you can receive error notifications.

.. _error-handlers:

Error handlers
--------------

You might want to show custom error pages to the user when an error occurs.
This can be done by registering error handlers.

Error handlers are normal :ref:`views` but instead of being registered for
routes they are registered for exceptions that are rised while trying to
do something else.

Registering
```````````

Register error handlers using :meth:`~flask.Flask.errorhandler` or
:meth:`~flask.Flask.register_error_handler`::

    @app.errorhandler(werkzeug.exceptions.BadRequest)
    def handle_bad_request(e):
        return 'bad request!'
    
    app.register_error_handler(400, lambda e: 'bad request!')

Those two ways are equivalent, but the first one is more clear and leaves
you with a function to call on your whim (and in tests).  Note that
:exc:`werkzeug.exceptions.HTTPException` subclasses like
:exc:`~werkzeug.exceptions.BadRequest` from the example and their HTTP codes
are interchangeable when handed to the registration methods or decorator
(``BadRequest.code == 400``).

You are however not limited to :exc:`~werkzeug.exceptions.HTTPException`
or HTTP status codes but can register a handler for every exception class you
like.

.. versionchanged:: 0.11

   Errorhandlers are now prioritized by specificity of the exception classes
   they are registered for instead of the order they are registered in.

Handling
````````

Once an exception instance is raised, its class hierarchy is traversed,
and searched for in the exception classes for which handlers are registered.
The most specific handler is selected.

E.g. if an instance of :exc:`ConnectionRefusedError` is raised, and a handler
is registered for :exc:`ConnectionError` and :exc:`ConnectionRefusedError`,
the more specific :exc:`ConnectionRefusedError` handler is called on the
exception instance, and its response is shown to the user.

Error Mails
-----------

If the application runs in production mode (which it will do on your
server) you might not see any log messages.  The reason for that is that
Flask by default will just report to the WSGI error stream or stderr
(depending on what's available).  Where this ends up is sometimes hard to
find.  Often it's in your webserver's log files.

I can pretty much promise you however that if you only use a logfile for
the application errors you will never look at it except for debugging an
issue when a user reported it for you.  What you probably want instead is
a mail the second the exception happened.  Then you get an alert and you
can do something about it.

Flask uses the Python builtin logging system, and it can actually send
you mails for errors which is probably what you want.  Here is how you can
configure the Flask logger to send you mails for exceptions::

    ADMINS = ['yourname@example.com']
    if not app.debug:
        import logging
        from logging.handlers import SMTPHandler
        mail_handler = SMTPHandler('127.0.0.1',
                                   'server-error@example.com',
                                   ADMINS, 'YourApplication Failed')
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

So what just happened?  We created a new
:class:`~logging.handlers.SMTPHandler` that will send mails with the mail
server listening on ``127.0.0.1`` to all the `ADMINS` from the address
*server-error@example.com* with the subject "YourApplication Failed".  If
your mail server requires credentials, these can also be provided.  For
that check out the documentation for the
:class:`~logging.handlers.SMTPHandler`.

We also tell the handler to only send errors and more critical messages.
Because we certainly don't want to get a mail for warnings or other
useless logs that might happen during request handling.

Before you run that in production, please also look at :ref:`logformat` to
put more information into that error mail.  That will save you from a lot
of frustration.


Logging to a File
-----------------

Even if you get mails, you probably also want to log warnings.  It's a
good idea to keep as much information around that might be required to
debug a problem.  By default as of Flask 0.11, errors are logged to your
webserver's log automatically.  Warnings however are not.  Please note
that Flask itself will not issue any warnings in the core system, so it's
your responsibility to warn in the code if something seems odd.

There are a couple of handlers provided by the logging system out of the
box but not all of them are useful for basic error logging.  The most
interesting are probably the following:

-   :class:`~logging.FileHandler` - logs messages to a file on the
    filesystem.
-   :class:`~logging.handlers.RotatingFileHandler` - logs messages to a file
    on the filesystem and will rotate after a certain number of messages.
-   :class:`~logging.handlers.NTEventLogHandler` - will log to the system
    event log of a Windows system.  If you are deploying on a Windows box,
    this is what you want to use.
-   :class:`~logging.handlers.SysLogHandler` - sends logs to a UNIX
    syslog.

Once you picked your log handler, do like you did with the SMTP handler
above, just make sure to use a lower setting (I would recommend
`WARNING`)::

    if not app.debug:
        import logging
        from themodule import TheHandlerYouWant
        file_handler = TheHandlerYouWant(...)
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)

.. _logformat:

Controlling the Log Format
--------------------------

By default a handler will only write the message string into a file or
send you that message as mail.  A log record stores more information,
and it makes a lot of sense to configure your logger to also contain that
information so that you have a better idea of why that error happened, and
more importantly, where it did.

A formatter can be instantiated with a format string.  Note that
tracebacks are appended to the log entry automatically.  You don't have to
do that in the log formatter format string.

Here some example setups:

Email
`````

::

    from logging import Formatter
    mail_handler.setFormatter(Formatter('''
    Message type:       %(levelname)s
    Location:           %(pathname)s:%(lineno)d
    Module:             %(module)s
    Function:           %(funcName)s
    Time:               %(asctime)s

    Message:

    %(message)s
    '''))

File logging
````````````

::

    from logging import Formatter
    file_handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))


Complex Log Formatting
``````````````````````

Here is a list of useful formatting variables for the format string.  Note
that this list is not complete, consult the official documentation of the
:mod:`logging` package for a full list.

.. tabularcolumns:: |p{3cm}|p{12cm}|

+------------------+----------------------------------------------------+
| Format           | Description                                        |
+==================+====================================================+
| ``%(levelname)s``| Text logging level for the message                 |
|                  | (``'DEBUG'``, ``'INFO'``, ``'WARNING'``,           |
|                  | ``'ERROR'``, ``'CRITICAL'``).                      |
+------------------+----------------------------------------------------+
| ``%(pathname)s`` | Full pathname of the source file where the         |
|                  | logging call was issued (if available).            |
+------------------+----------------------------------------------------+
| ``%(filename)s`` | Filename portion of pathname.                      |
+------------------+----------------------------------------------------+
| ``%(module)s``   | Module (name portion of filename).                 |
+------------------+----------------------------------------------------+
| ``%(funcName)s`` | Name of function containing the logging call.      |
+------------------+----------------------------------------------------+
| ``%(lineno)d``   | Source line number where the logging call was      |
|                  | issued (if available).                             |
+------------------+----------------------------------------------------+
| ``%(asctime)s``  | Human-readable time when the LogRecord` was        |
|                  | created.  By default this is of the form           |
|                  | ``"2003-07-08 16:49:45,896"`` (the numbers after   |
|                  | the comma are millisecond portion of the time).    |
|                  | This can be changed by subclassing the formatter   |
|                  | and overriding the                                 |
|                  | :meth:`~logging.Formatter.formatTime` method.      |
+------------------+----------------------------------------------------+
| ``%(message)s``  | The logged message, computed as ``msg % args``     |
+------------------+----------------------------------------------------+

If you want to further customize the formatting, you can subclass the
formatter.  The formatter has three interesting methods:

:meth:`~logging.Formatter.format`:
    handles the actual formatting.  It is passed a
    :class:`~logging.LogRecord` object and has to return the formatted
    string.
:meth:`~logging.Formatter.formatTime`:
    called for `asctime` formatting.  If you want a different time format
    you can override this method.
:meth:`~logging.Formatter.formatException`
    called for exception formatting.  It is passed an :attr:`~sys.exc_info`
    tuple and has to return a string.  The default is usually fine, you
    don't have to override it.

For more information, head over to the official documentation.


Other Libraries
---------------

So far we only configured the logger your application created itself.
Other libraries might log themselves as well.  For example, SQLAlchemy uses
logging heavily in its core.  While there is a method to configure all
loggers at once in the :mod:`logging` package, I would not recommend using
it.  There might be a situation in which you want to have multiple
separate applications running side by side in the same Python interpreter
and then it becomes impossible to have different logging setups for those.

Instead, I would recommend figuring out which loggers you are interested
in, getting the loggers with the :func:`~logging.getLogger` function and
iterating over them to attach handlers::

    from logging import getLogger
    loggers = [app.logger, getLogger('sqlalchemy'),
               getLogger('otherlibrary')]
    for logger in loggers:
        logger.addHandler(mail_handler)
        logger.addHandler(file_handler)


Debugging Application Errors
============================

For production applications, configure your application with logging and
notifications as described in :ref:`application-errors`.  This section provides
pointers when debugging deployment configuration and digging deeper with a
full-featured Python debugger.


When in Doubt, Run Manually
---------------------------

Having problems getting your application configured for production?  If you
have shell access to your host, verify that you can run your application
manually from the shell in the deployment environment.  Be sure to run under
the same user account as the configured deployment to troubleshoot permission
issues.  You can use Flask's builtin development server with `debug=True` on
your production host, which is helpful in catching configuration issues, but
**be sure to do this temporarily in a controlled environment.** Do not run in
production with `debug=True`.


.. _working-with-debuggers:

Working with Debuggers
----------------------

To dig deeper, possibly to trace code execution, Flask provides a debugger out
of the box (see :ref:`debug-mode`).  If you would like to use another Python
debugger, note that debuggers interfere with each other.  You have to set some
options in order to use your favorite debugger:

* ``debug``        - whether to enable debug mode and catch exceptions
* ``use_debugger`` - whether to use the internal Flask debugger
* ``use_reloader`` - whether to reload and fork the process on exception

``debug`` must be True (i.e., exceptions must be caught) in order for the other
two options to have any value.

If you're using Aptana/Eclipse for debugging you'll need to set both
``use_debugger`` and ``use_reloader`` to False.

A possible useful pattern for configuration is to set the following in your
config.yaml (change the block as appropriate for your application, of course)::

   FLASK:
       DEBUG: True
       DEBUG_WITH_APTANA: True

Then in your application's entry-point (main.py), you could have something like::

   if __name__ == "__main__":
       # To allow aptana to receive errors, set use_debugger=False
       app = create_app(config="config.yaml")

       if app.debug: use_debugger = True
       try:
           # Disable Flask's debugger if external debugger is requested
           use_debugger = not(app.config.get('DEBUG_WITH_APTANA'))
       except:
           pass
       app.run(use_debugger=use_debugger, debug=app.debug,
               use_reloader=use_debugger, host='0.0.0.0')
