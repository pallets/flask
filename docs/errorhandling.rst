.. _application-errors:

Handling Application Errors
===========================

.. versionadded:: 0.3

Applications fail, server fail.  Sooner or later you will see an exception
in production.  Even if your code is 100% correct, you will still see
exceptions from time to time.  Why?  Because everything else involved will
fail.  Here some situations where perfectly fine code can lead to server
errors:

-   the client terminated the request early and the application was still
    reading from the incoming data.
-   the database server was overloaded and could not handle the query.
-   a filesystem is full
-   a harddrive crashed
-   a backend server overloaded
-   a programming error in a library you are using
-   network connection of the server to another system failed.

And that's just a small sample of issues you could be facing.  So how to
deal with that sort of problem?  By default if your application runs in
production mode, Flask will display a very simple page for you and log the
exception to the :attr:`~flask.Flask.logger`.

But there is more you can do, and we will cover some better setups to deal
with errors.

Error Mails
-----------

If the application runs in production mode (which it will do on your
server) you won't see any log messages by default.  Why that?  Flask tries
to be a zero-configuration framework and where should it drop the logs for
you if there is no configuration.  Guessing is not a good idea because
chances are, the place it guessed is not the place where the user has the
permission to create a logfile.  Also, for most small applications nobody
will look at the logs anyways.

In fact, I promise you right now that if you configure a logfile for the
application errors you will never look at it except for debugging an issue
when a user reported it for you.  What you want instead is a mail the
second the exception happened.  Then you get an alert and you can do
something about it.

Flask is using the Python builtin logging system and that one can actually
send you mails for errors which is probably what you want.  Here is how
you can configure the Flask logger to send you mails for exceptions::

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
your mail server requires credentials these can also provided, for that
check out the documentation for the :class:`~logging.handlers.SMTPHandler`.

We also tell the handler to only send errors and more critical messages.
Because we certainly don't want to get a mail for warnings or other
useless logs that might happen during request handling.

Before you run that in production, please also look at :ref:`log-format`
to put more information into that error mail.  That will save you from a
lot of frustration.


Logging to a File
-----------------

Even if you get mails, you probably also want to log warnings.  It's a
good idea to keep as much information around that might be required to
debug a problem.  Please note that Flask itself will not issue any
warnings in the core system, so it's your responsibility to warn in the
code if something seems odd.

There are a couple of handlers provided by the logging system out of the
box but not all of them are useful for basic error logging.  The most
interesting are probably the following:

-   :class:`~logging.handlers.FileHandler` - logs messages to a file on the
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
        from logging.handlers import TheHandlerYouWant
        file_handler = TheHandlerYouWant(...)
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)

.. _log-format:

Controlling the Log Format
--------------------------

By default a handler will only write the message string into a file or
send you that message as mail.  But a log record stores more information
and it makes a lot of sense to configure your logger to also contain that
information so that you have a better idea of why that error happened, and
more importantly, where it did.

A formatter can be instanciated with a format string.  Note that
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
    called for exception formatting.  It is passed a :attr:`~sys.exc_info`
    tuple and has to return a string.  The default is usually fine, you
    don't have to override it.

For more information, head over to the official documentation.


Other Libraries
---------------

So far we only configured the logger your application created itself.
Other libraries might log themselves as well.  For example, SQLAlchemy use
logging heavily in the core.  While there is a method to configure all
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
