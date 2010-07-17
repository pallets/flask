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
signal.  This however might not be true for Flask extensions, so consult
the documentation when subscribing to signals.

Additionally there is a convenient helper method that allows you to
temporarily subscribe a function to a signal.  This is especially helpful
for unittests (:meth:`~blinker.base.Signal.temporarily_connected_to`).
This has to be used in combination with the `with` statement.

Here for example a helper context manager that can be used to figure out
in a unittest which templates were rendered and what variables were passed
to the template::

    from flask import template_rendered
    from contextlib import contextmanager

    @contextmanager
    def captured_templates():
        recorded = []
        def record(template, context):
            recorded.append((template, context))
        template_rendered.connect(record)
        try:
            yield templates
        finally:
            template_rendered.disconnect(record)

This can now easily be paired with a test client::

    with captured_templates() as templates:
        rv = app.test_client().get('/')
        assert rv.status_code == 200
        assert len(templates) == 1
        template, context = templates[0]
        assert template.name == 'index.html'
        assert len(context['items']) == 10

All the template rendering in the code, the `with` block wraps will now be
recorded in the `templates` variable.  Whenever a template is rendered,
the template object as well as context is appended to it.

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

   If you are writing a Flask extension and you to gracefully degrade for
   missing blinker installations, you can do so by using the
   :class:`flask.signals.Namespace` class.

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

        def log_template_renders(sender, template, context):
            sender.logger.debug('Rendering template "%s" with context %s',
                                template.name or 'string template',
                                context)

        from flask import request_started
        request_started.connect(log_template_renders)

.. data:: flask.request_started
   :noindex:

   This signal is sent before any request processing started but when the
   request context was set up.  Because the request context is already
   bound, the subscriber can access the request with the standard global
   proxies such as :class:`~flask.request`.

   Example subscriber::

        def log_request(sender):
            sender.logger.debug('Request context is set up')

        from flask import request_started
        request_started.connect(log_request)

.. data:: flask.request_finished
   :noindex:

   This signal is sent right before the response is sent to the client.
   It is passed the response to be sent named `response`.

   Example subscriber::

        def log_response(sender, response):
            sender.logger.debug('Request context is about to close down.  '
                                'Response: %s', response)

        from flask import request_finished
        request_finished.connect(log_response)

.. data:: flask.got_request_exception
   :noindex:

   This signal is sent when an exception happens during request processing.
   It is sent *before* the standard exception handling kicks in and even
   in debug mode, where no exception handling happens.  The exception
   itself is passed to the subscriber as `exception`.

   Example subscriber::

        def log_exception(sender, exception):
            sender.logger.debug('Got exception during processing: %s', exception)

        from flask import got_request_exception
        got_request_exception.connect(log_exception)

.. _blinker: http://pypi.python.org/pypi/blinker
