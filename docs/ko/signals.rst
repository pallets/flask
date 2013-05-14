.. _signals:

시그널(Signals)
===============

.. versionadded:: 0.6

플라스크 0.6부터 시그널 지원 기능이 플라스크에 통합됐다.  이 기능은
`blinker`_ 라는 훌륭한 라이브러리로 제공되며 사용할 수 없을 경우
자연스럽게 지원하지 않는 상태로 돌아갈 것이다. 

시그널이란 무엇인가?  시그널은 핵심 프레임워크나 다른 플라스크 확장의
어느 곳에서 동작이 발생했을 때 공지를 보내어 어플리케이션을 동작하게 하여
어플리케이션간의 의존성을 분리하도록 돕는다.  요약하자면 시그널은 
특정 시그널 발신자가 어떤 일이 발생했다고 수신자에게 알려준다.

플라스크에는 여러 시그널이 있고 플라스크 확장은 더 많은 시그널을 제공할
수 도 있다.  또한 시그널은 수신자에게 무엇인가를 알리도록 의도한 것이지
수신자가 데이터를 변경하도록 권장하지 않아야 한다.  몇몇 빌트인 데코레이터의 
동작과 같은 것을 하는 것 처럼 보이는 시그널이 있다는 것을 알게될 것이다.
(예를 들면 :data:`~flask.request_started` 은 
:meth:`~flask.Flask.before_request` 과 매우 유사하다) 하지만, 그 동작 방식에
차이는 있다.  예제의 핵심 :meth:`~flask.Flask.before_request` 핸들러는 정해진
순서에 의해 실행되고 응답이 반환됨에 의해 일찍 요청처리를 중단할 수 있다.  
반면에 다른 모든 시그널은 정해진 순서 없이 실행되며 어떤 데이터도 수정하지 않는다.

핸들러 대비 시그널의 큰 장점은 짧은 순간 동안 그 시그널을 안전하게 수신할 수
있다는 것이다.  예를 들면 이런 일시적인 수신은 단위테스팅에 도움이 된다.
여러분이 요청의 일부분으로 어떤 템플릿을 보여줄지 알고 싶다고 해보자: 시그널이
정확히 바로 그 작업을 하게 한다.

시그널을 수신하기
-----------------

시그널은 수신하려면 시그널의 :meth:`~blinker.base.Signal.connect` 메소드를
사용할 수 있다. 첫번째 인자는 시그널이 송신됐을 때 호출되는 함수고, 선택적인
두번째 인자는 송신자를 지정한다.  해당 시그널의 송신을 중단하려면 
:meth:`~blinker.base.Signal.disconnect` 메소드를 사용하면 된다.

모든 핵심 플라스크 시그널에 대해서 송신자는 시그널을 발생하는 어플리케이션이다.
여러분이 시그널을 수신할 때, 모든 어플리케이션의 시그널을 수신하고 싶지 않다면
받고자하는 시그널의 송신자 지정을 잊지 말도록 해라.  여러분이 확장을 개발하고 있다면
특히나 주의해야한다.

예를 들면 여기에 단위테스팅에서 어떤 템플릿이 보여지고 어떤 변수가 템플릿으로 
전달되는지 이해하기 위해 사용될 수 있는 헬퍼 컨택스트 매니저가 있다::

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

위의 메소드는 테스트 클라이언트와 쉽게 묶일 수 있다::

    with captured_templates(app) as templates:
        rv = app.test_client().get('/')
        assert rv.status_code == 200
        assert len(templates) == 1
        template, context = templates[0]
        assert template.name == 'index.html'
        assert len(context['items']) == 10

플라스크가 시그널에 새 인자를 알려준다면 여러분이 호출한 메소드는
실패하지 않을 것이므로 추가적인 ``**extra`` 인자로 수신하도록 해라.

`with` 블럭의 내용에 있는 어플리케이션 `app`이 생성한 코드에서 보여주는
모든 템플릿은 `templates` 변수에 기록될 것이다.  템플릿이 그려질 때마다
컨텍스트 뿐만 아니라 템플릿 객체도 어플리케이션에 덧붙여진다.

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

        from flask import appcontext_tearing_down
        appcontext_tearing_down.connect(close_db_connection, app)

   This will also be passed an `exc` keyword argument that has a reference
   to the exception that caused the teardown if there was one.

.. _blinker: http://pypi.python.org/pypi/blinker
