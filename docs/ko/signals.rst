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

`with` 블럭의 내용에 있는 어플리케이션 `app` 이 생성한 코드에서 보여주는
모든 템플릿은 `templates` 변수에 기록될 것이다.  템플릿이 그려질 때마다
컨텍스트 뿐만 아니라 템플릿 객체도 어플리케이션에 덧붙여진다.

부가적으로 편리한 헬퍼 메소드도 존재한다(:meth:`~blinker.base.Signal.connected_to`).
그 메소드는 일시적으로 그 자체에 컨텍스트 메니저를 가진 시그널에 대한 함수를 수신한다.
컨텍스트 매니저의 반환값을 그런 방식으로 지정할 수 없기 때문에 인자로 템플릿의 목록을 
넘겨줘야 한다::

    from flask import template_rendered

    def captured_templates(app, recorded, **extra):
        def record(sender, template, context):
            recorded.append((template, context))
        return template_rendered.connected_to(record, app)

위의 예제는 아래처럼 보일 수 있다::

    templates = []
    with captured_templates(app, templates, **extra):
        ...
        template, context = templates[0]

.. admonition:: Blinker API 변경내용

   :meth:`~blinker.base.Signal.connected_to` 메소드는 Blinker 
   버전 1.1에 나왔다.

시그널 생성하기
---------------

여러분이 어플리케이션에서 시그널을 사용하고 싶다면, 직접 blinker 라이브러리를
사용할 수 있다.  가장 일반적인 사용예는 변경된 :class:`~blinker.base.Namespace`. 
클래스에 시그널을 명명하는 것이다. 이것이 보통 권고되는 방식이다::

    from blinker import Namespace
    my_signals = Namespace()

이제 여러분은 아래와 같이 새 시그널을 생성할 수 있다::

    model_saved = my_signals.signal('model-saved')

여기에서 시그널에 이름을 준것은 시그널은 구분해주고 또한 디버깅을
단순화한다.  :attr:`~blinker.base.NamedSignal.name` 속성으로 시그널에
부여된 이름을 얻을 수 있다.

.. admonition:: 플라스크 확장 개발자를 위해서

   여러분이 플라스크 확장을 개발하고 있고 blinker 설치를 놓친것에 대해 부드럽게
   대처하고 싶다면, :class:`flask.signals.Namespace` 클래스를 사용할 수 있다.

.. _signals-sending:

시그널 보내기
-------------

시그널을 전송하고 싶다면, :meth:`~blinker.base.Signal.send` 메소드를 호출하면 된다.
이 메소드는 첫번째 인자로 송신자를 넘겨주고 선택적으로 시그널 수신자에게 전달되는
키워드 인자도 있다::

    class Model(object):
        ...

        def save(self):
            model_saved.send(self)

항상 좋은 송신자를 뽑도록 한다.  여러분이 시그널을 보내는 클래스를 갖는다면
송신자로 `self` 를 넘겨준다.  여러분이 임의의 함수에서 시그널을 전송한다면,
``current_app._get_current_object()`` 를 송신자로 전달할 수 있다.

.. admonition:: 송신자로 프락시를 넘겨주기

   시그널의 송신자로 절대 :data:`~flask.current_app` 를 넘겨주지 않도록 하고
   대신 ``current_app._get_current_object()`` 를 사용한다.  왜냐하면
   :data:`~flask.current_app` 는 실제 어플리케이션 객체가 아닌 프락시 객체이기
   때문이다.


시그널과 플라스크 요청 컨텍스트
-------------------------------

시그널을 수신할 때 :ref:`request-context` 를 완전하게 지원한다. Context-local
변수는 :data:`~flask.request_started` 과 :data:`~flask.request_finished` 사이에서
일관성을 유지하므로 여러분은 필요에 따라 :class:`flask.g` 과 다른 변수를 참조할
수 있다.  :ref:`signals-sending` 과 :data:`~flask.request_tearing_down` 시그널에서
언급하는 제약에 대해 유의한다.


시그널 수신 기반 데코레이터
---------------------------

Blinker 1.1 과 함께 여러분은 또한 :meth:`~blinker.base.NamedSignal.connect_via`
데코레이터를 사용하여 시그널을 쉽게 수신할 수 있다::

    from flask import template_rendered

    @template_rendered.connect_via(app)
    def when_template_rendered(sender, template, context, **extra):
        print 'Template %s is rendered with %s' % (template.name, context)

핵심 시그널
-----------

.. 이 목록이 수정될 때, api.rst에 있는 목록 또한 갱신되야 한다.

플라스크에는 다음과 같은 시그널이 존재한다:

.. data:: flask.template_rendered
   :noindex:

   이 시그널은 템플릿이 성공적으로 뿌려졌을 때 송신된다.  이 시그널은
   `template` 으로 템플릿과 딕셔너리 형태인 `context` 로 컨텍스트를
   인스턴스로 하여 호출된다.

   수신 예제::

        def log_template_renders(sender, template, context, **extra):
            sender.logger.debug('Rendering template "%s" with context %s',
                                template.name or 'string template',
                                context)

        from flask import template_rendered
        template_rendered.connect(log_template_renders, app)

.. data:: flask.request_started
   :noindex:

   이 시그널은 요청 처리가 시작되기 전이지만 요청 컨텍스트는 만들어졌을 때
   송신된다.  요청 컨텍스트가 이미 연결됐기 때문에, 수신자는 표준 전역 프록시
   객체인 :class:`~flask.request` 으로 요청을 참조할 수 있다.

   수신 예제::

        def log_request(sender, **extra):
            sender.logger.debug('Request context is set up')

        from flask import request_started
        request_started.connect(log_request, app)

.. data:: flask.request_finished
   :noindex:

   이 시그널은 클라이언트로 응답이 가기 바로 전에 보내진다. `response` 인자로
   응답 객체를 넘겨준다.

   수신 예제::

        def log_response(sender, response, **extra):
            sender.logger.debug('Request context is about to close down.  '
                                'Response: %s', response)

        from flask import request_finished
        request_finished.connect(log_response, app)

.. data:: flask.got_request_exception
   :noindex:

   이 시그널은 요청 처리 동안 예외가 발생했을 때 보내진다.  표준 예외처리가
   *시작되기 전에* 송신되고 예외 처리를 하지 않는 디버깅 환경에서도 보내진다.
   `exception` 인자로 예외 자체가 수신자에게 넘어간다.

   수신 예제::

        def log_exception(sender, exception, **extra):
            sender.logger.debug('Got exception during processing: %s', exception)

        from flask import got_request_exception
        got_request_exception.connect(log_exception, app)

.. data:: flask.request_tearing_down
   :noindex:

   이 시그널은 요청 객체가 제거될 때 보내진다.  요청 처리 과정에서 요류가
   발생하더라도 항상 호출된다.  현재 시그널을 기다리고 있는 함수는 일반
   teardown 핸들러 뒤에 호출되지만, 순서를 보장하지는 않는다.

   수신 예제::

        def close_db_connection(sender, **extra):
            session.close()

        from flask import request_tearing_down
        request_tearing_down.connect(close_db_connection, app)

   플라스크 0.9에서, 예외가 있는 경우 이 시그널을 야기하는 예외에 대한
   참조를 갖는 'exc' 키워드 인자를 또한 넘겨줄 것이다.

.. data:: flask.appcontext_tearing_down
   :noindex:

   이 시그널은 어플리케이션 컨텍스트가 제거될 때 보내진다.  예외가 발생하더라도
   이 시그널은 항상 호출되고, 일반 teardown 핸들러 뒤에 시그널에 대한 콜백 함수가
   호출되지만, 순서는 보장하지 않는다.

   수신 예제::

        def close_db_connection(sender, **extra):
            session.close()

        from flask import appcontext_tearing_down
        appcontext_tearing_down.connect(close_db_connection, app)

   'request_tearing_down' 과 마찬가지로 예외에 대한 참조를 `exc` 키워드 인자로
   넘겨줄 것이다.

.. _blinker: http://pypi.python.org/pypi/blinker
