.. _signals:

Signals
=======

.. versionadded:: 0.6

Starting with Flask 0.6, there is integrated support for signalling in
Flask.  This support is provided by the excellent `blinker`_ library and
will gracefully fall back if it is not available.

What are signals?  Signals help you decouple applications by sending
notifications when actions occur elsewhere in the core framework or
another Flask extensions.  In short, signals allow certain senders to
notify subscribers that something happened.

Flask comes with a couple of signals and other extensions might provide
more.  Also keep in mind that signals are intended to notify subscribers
and should not encourage subscribers to modify data.  You will notice that
there are signals that appear to do the same thing like some of the
builtin decorators do (eg: :data:`~flask.request_started` is very similar
to :meth:`~flask.Flask.before_request`).  There are however difference in
how they work.  The core :meth:`~flask.Flask.before_request` handler for
example is executed in a specific order and is able to abort the request
early by returning a response.  In contrast all signal handlers are
executed in undefined order and do not modify any data.

The big advantage of signals over handlers is that you can safely
subscribe to them for the split of a second.  These temporary
subscriptions are helpful for unittesting for example.  Say you want to
know what templates were rendered as part of a request: signals allow you
to do exactly that.

Subscribing to Signals
----------------------

To subscribe to a signal, you can use the
:meth:`~blinker.base.Signal.connect` method of a signal.  The first
argument is the function that should be called when the signal is emitted,
the optional second argument specifies a sender.  To unsubscribe from a
signal, you can use the :meth:`~blinker.base.Signal.disconnect` method.

For all core Flask signals, the sender is the application that issued the
signal.  When you subscribe to a signal, be sure to also provide a sender
unless you really want to listen for signals of all applications.  This is
especially true if you are developing an extension.

Here for example a helper context manager that can be used to figure out
in a unittest which templates were rendered and what variables were passed
to the template::

    from flask import template_rendered
    from contextlib import contextmanager

    @contextmanager
    def captured_templates(app):
        recorded = []
        def record(sender, template, context, **extra):
            recorded.append((template, context))
        template_rendered.connect(record, app)
        try:
            yield recorded
        finally:
            template_rendered.disconnect(record, app)

This can now easily be paired with a test client::

    with captured_templates(app) as templates:
        rv = app.test_client().get('/')
        assert rv.status_code == 200
        assert len(templates) == 1
        template, context = templates[0]
        assert template.name == 'index.html'
        assert len(context['items']) == 10

Make sure to subscribe with an extra ``**extra`` argument so that your
calls don't fail if Flask introduces new arguments to the signals.

All the template rendering in the code issued by the application `app`
in the body of the `with` block will now be recorded in the `templates`
variable.  Whenever a template is rendered, the template object as well as
context are appended to it.

Additionally there is a convenient helper method
(:meth:`~blinker.base.Signal.connected_to`).  that allows you to
temporarily subscribe a function to a signal with a context manager on
its own.  Because the return value of the context manager cannot be
specified that way one has to pass the list in as argument::

    from flask import template_rendered

    def captured_templates(app, recorded, **extra):
        def record(sender, template, context):
            recorded.append((template, context))
        return template_rendered.connected_to(record, app)

The example above would then look like this::

    templates = []
    with captured_templates(app, templates, **extra):
        ...
        template, context = templates[0]

.. admonition:: Blinker API Changes

   The :meth:`~blinker.base.Signal.connected_to` method arrived in Blinker
   with version 1.1.

Creating Signals
----------------

If you want to use signals in your own application, you can use the
blinker library directly.  The most common use case are named signals in a
custom :class:`~blinker.base.Namespace`..  This is what is recommended
most of the time::

    from blinker import Namespace
    my_signals = Namespace()

Now you can create new signals like this::

    model_saved = my_signals.signal('model-saved')

The name for the signal here makes it unique and also simplifies
debugging.  You can access the name of the signal with the
:attr:`~blinker.base.NamedSignal.name` attribute.

.. admonition:: For Extension Developers

   If you are writing a Flask extension and you want to gracefully degrade for
   missing blinker installations, you can do so by using the
   :class:`flask.signals.Namespace` class.

.. _signals-sending:

Sending Signals
---------------

If you want to emit a signal, you can do so by calling the
:meth:`~blinker.base.Signal.send` method.  It accepts a sender as first
argument and optionally some keyword arguments that are forwarded to the
signal subscribers::

    class Model(object):
        ...

        def save(self):
            model_saved.send(self)

Try to always pick a good sender.  If you have a class that is emitting a
signal, pass `self` as sender.  If you emitting a signal from a random
function, you can pass ``current_app._get_current_object()`` as sender.

.. admonition:: Passing Proxies as Senders

   Never pass :data:`~flask.current_app` as sender to a signal.  Use
   ``current_app._get_current_object()`` instead.  The reason for this is
   that :data:`~flask.current_app` is a proxy and not the real application
   object.


Signals and Flask's Request Context
-----------------------------------

Signals fully support :ref:`request-context` when receiving signals.
Context-local variables are consistently available between
:data:`~flask.request_started` and :data:`~flask.request_finished`, so you can
rely on :class:`flask.g` and others as needed.  Note the limitations described
in :ref:`signals-sending` and the :data:`~flask.request_tearing_down` signal.


Decorator Based Signal Subscriptions
------------------------------------

With Blinker 1.1 you can also easily subscribe to signals by using the new
:meth:`~blinker.base.NamedSignal.connect_via` decorator::

    from flask import template_rendered

    @template_rendered.connect_via(app)
    def when_template_rendered(sender, template, context, **extra):
        print 'Template %s is rendered with %s' % (template.name, context)

Core Signals
------------

.. when modifying this list, also update the one in api.rst

The following signals exist in Flask:

.. data:: flask.template_rendered
   :noindex:

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

.. data:: flask.request_started
   :noindex:

   This signal is sent before any request processing started but when the
   request context was set up.  Because the request context is already
   bound, the subscriber can access the request with the standard global
   proxies such as :class:`~flask.request`.

   Example subscriber::

        def log_request(sender, **extra):
            sender.logger.debug('Request context is set up')

        from flask import request_started
        request_started.connect(log_request, app)

.. data:: flask.request_finished
   :noindex:

   This signal is sent right before the response is sent to the client.
   It is passed the response to be sent named `response`.

   Example subscriber::

        def log_response(sender, response, **extra):
            sender.logger.debug('Request context is about to close down.  '
                                'Response: %s', response)

        from flask import request_finished
        request_finished.connect(log_response, app)

.. data:: flask.got_request_exception
   :noindex:

   This signal is sent when an exception happens during request processing.
   It is sent *before* the standard exception handling kicks in and even
   in debug mode, where no exception handling happens.  The exception
   itself is passed to the subscriber as `exception`.

   Example subscriber::

        def log_exception(sender, exception, **extra):
            sender.logger.debug('Got exception during processing: %s', exception)

        from flask import got_request_exception
        got_request_exception.connect(log_exception, app)

.. data:: flask.request_tearing_down
   :noindex:

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

.. data:: flask.appcontext_tearing_down
   :noindex:

   This signal is sent when the app context is tearing down.  This is always
   called, even if an exception is caused.  Currently functions listening
   to this signal are called after the regular teardown handlers, but this
   is not something you can rely on.

   Example subscriber::

        def close_db_connection(sender, **extra):
            session.close()

        from flask import request_tearing_down
        appcontext_tearing_down.connect(close_db_connection, app)

   This will also be passed an `exc` keyword argument that has a reference
   to the exception that caused the teardown if there was one.

.. _blinker: http://pypi.python.org/pypi/blinker
