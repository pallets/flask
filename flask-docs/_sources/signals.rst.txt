Signals
=======

Signals are a lightweight way to notify subscribers of certain events during the
lifecycle of the application and each request. When an event occurs, it emits the
signal, which calls each subscriber.

Signals are implemented by the `Blinker`_ library. See its documentation for detailed
information. Flask provides some built-in signals. Extensions may provide their own.

Many signals mirror Flask's decorator-based callbacks with similar names. For example,
the :data:`.request_started` signal is similar to the :meth:`~.Flask.before_request`
decorator. The advantage of signals over handlers is that they can be subscribed to
temporarily, and can't directly affect the application. This is useful for testing,
metrics, auditing, and more. For example, if you want to know what templates were
rendered at what parts of what requests, there is a signal that will notify you of that
information.


Core Signals
------------

See :ref:`core-signals-list` for a list of all built-in signals. The :doc:`lifecycle`
page also describes the order that signals and decorators execute.


Subscribing to Signals
----------------------

To subscribe to a signal, you can use the
:meth:`~blinker.base.Signal.connect` method of a signal.  The first
argument is the function that should be called when the signal is emitted,
the optional second argument specifies a sender.  To unsubscribe from a
signal, you can use the :meth:`~blinker.base.Signal.disconnect` method.

For all core Flask signals, the sender is the application that issued the
signal.  When you subscribe to a signal, be sure to also provide a sender
unless you really want to listen for signals from all applications.  This is
especially true if you are developing an extension.

For example, here is a helper context manager that can be used in a unit test
to determine which templates were rendered and what variables were passed
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
in the body of the ``with`` block will now be recorded in the `templates`
variable.  Whenever a template is rendered, the template object as well as
context are appended to it.

Additionally there is a convenient helper method
(:meth:`~blinker.base.Signal.connected_to`)  that allows you to
temporarily subscribe a function to a signal with a context manager on
its own.  Because the return value of the context manager cannot be
specified that way, you have to pass the list in as an argument::

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

Creating Signals
----------------

If you want to use signals in your own application, you can use the
blinker library directly.  The most common use case are named signals in a
custom :class:`~blinker.base.Namespace`.  This is what is recommended
most of the time::

    from blinker import Namespace
    my_signals = Namespace()

Now you can create new signals like this::

    model_saved = my_signals.signal('model-saved')

The name for the signal here makes it unique and also simplifies
debugging.  You can access the name of the signal with the
:attr:`~blinker.base.NamedSignal.name` attribute.

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
signal, pass ``self`` as sender.  If you are emitting a signal from a random
function, you can pass ``current_app._get_current_object()`` as sender.

.. admonition:: Passing Proxies as Senders

   Never pass :data:`~flask.current_app` as sender to a signal.  Use
   ``current_app._get_current_object()`` instead.  The reason for this is
   that :data:`~flask.current_app` is a proxy and not the real application
   object.


Signals and Flask's Request Context
-----------------------------------

Signals fully support :doc:`reqcontext` when receiving signals.
Context-local variables are consistently available between
:data:`~flask.request_started` and :data:`~flask.request_finished`, so you can
rely on :class:`flask.g` and others as needed.  Note the limitations described
in :ref:`signals-sending` and the :data:`~flask.request_tearing_down` signal.


Decorator Based Signal Subscriptions
------------------------------------

You can also easily subscribe to signals by using the
:meth:`~blinker.base.NamedSignal.connect_via` decorator::

    from flask import template_rendered

    @template_rendered.connect_via(app)
    def when_template_rendered(sender, template, context, **extra):
        print(f'Template {template.name} is rendered with {context}')


.. _blinker: https://pypi.org/project/blinker/
