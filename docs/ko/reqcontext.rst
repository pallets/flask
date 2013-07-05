.. _request-context:

요청 컨텍스트
===================

이 문서는 플라스크 0.7에 있는 동작을 설명하는데 대부분은 이전 버전과 비슷하지만, 몇몇 작고 
미묘한 차이를 갖는다. 

13장인 어플리케이션 컨텍스트 :ref:`app-context` 을 먼저 읽는 것을 권고한다. 


컨텍스트 로컬로 다이빙하기
--------------------------

여러분이 사용자를 리디렉트해야하는 URL을 반환하는 유틸리티 함수를 갖는다고 하자. 그 함수는 
항상 URL의 next 인자나 HTTP referer 또는 index에 대한 URL을 리디렉트한다고 가정하자::

    from flask import request, url_for

    def redirect_url():
        return request.args.get('next') or \
               request.referrer or \
               url_for('index')

여러분이 볼 수 있는 것처럼, 그것은 요청 객체를 접근한다. 여러분은 플레인 파이썬 쉘에서 
이것을 실행하면, 여러분은 아래와 같은 예외를 볼 것이다: 


>>> redirect_url()
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
AttributeError: 'NoneType' object has no attribute 'request'


우리가 현재 접근할 수 있는 요청을 갖고 있지 않기 때문에 그것은 이해가 된다. 그래서 우리는 
요청을 만들고 그것을 현재 컨텍스트에 연결시켜야 한다. 
:attr:`~flask.Flask.test_request_context` 메소드는 우리에게 
:class:`~flask.ctx.RequestContext` 를 만들어 줄 수 있다: 


>>> ctx = app.test_request_context('/?next=http://example.com/')

이 컨텍스트는 두 가지 방식으로 사용될 수 있다. `with` 절과 함께 사용되거나 
:meth:`~flask.ctx.RequestContext.push` 와 :meth:`~flask.ctx.RequestContext.pop` 메소드를 호출하여 사용된다: 


>>> ctx.push()

이 시점부터 여러분은 요청 객체를 가지고 작업할 수 있다 :

>>> redirect_url()
u'http://example.com/'

`pop` 함수를 호출할 때까지:

>>> ctx.pop()

요청 컨텍스트는 내부적으로 스택을 유지하기 때문에 여러분은 여러번 push와 pop을 할 수 있다. 
이것이 내부적인 리디렉트와 같은 것을 손쉽게 구현한 것이다. 

상호작용 파이썬 쉘로부터 요청 컨텍스트를 사용하는 더 많은 정보는 :ref:`shell` 장으로 넘어가라. 


컨텍스트가 작동하는 방식
---------------------

여러분이 플라스크 WSGI 어플리케이션이 내부적으로 동작하는 방식을 살펴보려면, 아래와 대단히 
유사한 코드를 찾게될 것이다::


    def wsgi_app(self, environ):
        with self.request_context(environ):
            try:
                response = self.full_dispatch_request()
            except Exception, e:
                response = self.make_response(self.handle_exception(e))
            return response(environ, start_response)

:meth:`~Flask.request_context` 메소드는 새로운 :class:`~flask.ctx.RequestContext`  객체를 반환하고 컨텍스트를 연결하기 위해 `with` 구문과 조합하여 
RequestContext 객체를 사용한다. 이 시점부터 `with` 구문의 끝까지 같은 
쓰레드에서 호출되는 모든 것은 요청 글로벌 객체( :data:`flask.request` 와 기타 다른것들)에 접근할 수 있을 것이다. 

요청 컨텍스트도 내부적으로 스택처럼 동작한다. 
스택의 가장 상위에는 현재 활성화된 요청이 있다. 
:meth:`~flask.ctx.RequestContext.push` 는 스택의 제일 위에 컨텍스트를 더하고, :meth:`~flask.ctx.RequestContext.pop` 은 스택으로부터 제일 상위에 있는 컨텍스트를 제거한다. 
컨텍스트를 제거하는 pop 동작 시, 어플리케이션의 :func:`~flask.Flask.teardown_request`  함수 또한 실행된다. 

주목할 다른 것은 요청 컨텍스트가 들어오고 그때까지 해당 어플리케이션에 어떠한 어플리케이션 
컨텍스트가 없었다면, 자동으로 :ref:`application context <app-context>` 또한 생성할 것이라는 것이다. 

.. _callbacks-and-errors:

콜백과 오류
--------------------

Flask에서 요청 처리하는 동안 오류가 발생하면 어떻게 되는가? 버전 0.7에서 이 특별한 동작이 
변경되었는데, 왜냐하면 우리가 실제로 발생하는 것이 무엇인지 좀 더 쉽게 이해가기 원했기 
때문이다:

1.  각 요청 전에, :meth:`~flask.Flask.before_request` 함수들이 수행된다.
    이런 함수들 중 하나라도 응답을 반환하면, 다른 함수들은 더 이상 호출되지 않는다.
    그러나 어떤 경우라도 반환값은 뷰의 반환값에 대한 대체값으로 처리된다.

2.  :meth:`~flask.Flask.before_request` 함수들이 응닶을 반환하지 않는다면, 
    보통 요청 처리가 시작되고 요청에 맞는 뷰 함수가 응답을 반환하게 된다.

3.  그리고 나서, 뷰의 반환값은 실제 응답 객체로 변환되고 응답 객체를 대체하거나 변경할     
    준비가 되있는 :meth:`~flask.Flask.after_request` 함수로 전달된다.

4. 요청의 종료 시에는 :meth:`~flask.Flask.teardown_request` 함수가 실행된다.
   이 함수는 심지어 처리되지 않는 예외의 경우나 
   before-request 핸들러가 아직 처리되지 않거나 전혀 실해되지 않는 경우에도 항상 발생한다.
   (예를 들면, 테스트 환경에서 때때로 before-request 콜백이 호출되지 않기를 원할수도 있다.)

자 오류가 발생하면 무슨일이 발생하는가? 운영 환경에서는 예외가 처리되지 않으면, 500 내부 
서버 핸들러가 실행된다. 그러나, 개발 환경에서는 예외는 더 진행되지 않고 WSGI 서버로 영향을 
미친다. 대화형 디버거와 같은 방식에서는 도움되는 디버깅 정보를 제공할 수 있다. 

버전 0.7에서 중요한 변화는 내부 서버 오류가 더 이상 after-request 콜백에 의해 사후 
처리되지 않고 after-request 콜백이 실행되는 것을 보장해주지 않는다는 것이다. 이 방식으로 
내부 디스패칭 코드는 더 깔끔해졌고 커스터마이징과 이해가 더 쉬워졌다.

새로운 teardown 함수는 요청의 마지막에서 반드시 행이 필요한 경우에 대체할 목적으로 사용되는 것을 가정한다.


테어다운(Teardown) 콜백
------------------

테어다운 콜백은 특별한 콜백인데 여러 다른 시점에 실행되기 때문이다. 엄격하게 말하자면, 
그것들이 :class:`~flask.ctx.RequestContext` 객체의 생명주기와 연결되있긴 하지만, 그것들은 실제 요청 처리와  독립되있다. 요청 문맥이 꺼내질 때, :meth:`~flask.Flask.teardown_request` 함수는 호출된다. 

with 구문이  있는 테스트 클라이언트를 사용하여 요청 문맥의 생명이 범위가 늘었는지 또는 명령줄에서 요청 문맥을 사용할 때를 아는 것이 중요하다::

    with app.test_client() as client:
        resp = client.get('/foo')
        # the teardown functions are still not called at that point
        # even though the response ended and you have the response
        # object in your hand

    # only when the code reaches this point the teardown functions
    # are called.  Alternatively the same thing happens if another
    # request was triggered from the test client


명령줄에서 이 동작을 보기는 쉽다.:

>>> app = Flask(__name__)
>>> @app.teardown_request
... def teardown_request(exception=None):
...     print 'this runs after request'
...
>>> ctx = app.test_request_context()
>>> ctx.push()
>>> ctx.pop()
this runs after request
>>>

before-request 콜백은 아직 실행되지 않고 예외가 발생했더라도,teardown 콜백은 항상 
호출된다는 것을 명심하라. 테스트 시스템의 어떤 부분들 또한 before-request 핸들러를 
호출하지 않고 일시적으로 요청 문맥을 생성할지도 모른다. 절대로 실패하지 않는 방식으로 
여러분의 teardown-request 핸들러를 쓰는 것을 보장하라. 


.. _notes-on-proxies:


프록시에서 주의할 점
----------------

플라스크에서 제공하는 일부 객체들은 다른 객체에 대한 프록시들이다. 이렇게 하는 뒷 배경에는 
이런 프락시들이 쓰레들간에 공유되어 있고 그 프락시들이 쓰레드들에 연결된 실제 객체로 
필요시에 보이지 않게 디스패치되어야 한다는 것이다. 

대게 여러분은 그 프락시에 대해서 신경쓰지 않아도 되지만, 이 객체가 실제 프락시인지 알면 좋은 몇 가지 예외의 경우가 있다. :

-   프락시 객체들이 상속받은 타입을 속이지 않아서, 여러분이 실제 인스턴스를 확인한다면,    
    프락시로 된 인스턴스에서 타입을 확인해야한다.(아래의 `_get_current_object` 를 보라).

-   객체의 참조가 중요한 경우( :ref:`signals` 을 보내는 경우)

여러분이 프록시된 감춰진 객체에 접근할 필요가 있다면, :meth:`~werkzeug.local.LocalProxy._get_current_object` 메소드를 사용할 수 있다: 

    app = current_app._get_current_object()
    my_signal.send(app)


오류 시 컨텍스트 보존
-----------------------------

오류가 발생하거나 하지 않거나, 요청의 마지막에서 요청 문맥은 스택에서 빠지게 되고 그 문맥과 
관련된 모든 데이타는 소멸된다. 하지만, 개발하는 동안 그것은 예외가 발생하는 경우에 여러분이 
더 오랜 시간동안 그 정보를 갖고 있기를 원하기 때문에 문제가 될 수 있다. 플라스크 0.6과 그 
이전 버전의 디버그 모드에서는 예외가 발생했을 때, 요청 문맥이 꺼내지지 않아서 인터렉티브(
상호작용하는) 디버거가 여러분에게 여전히 중요한 정보를 제공할 수 있었다. 

플라스크 0.7부터 여러분은 ``PRESERVE_CONTEXT_ON_EXCEPTION`` 설정 변수값을 설정하여 그 
행동을 좀 더 세밀하게 설정한다. 디폴트로 이 설정은 ``DEBUG`` 설정과 연결된다.
어플리케이션이 디버그 모드라면, 그 문맥은 보존되지만, 운영 모드라면 보존되지 않는다. 

어플리케이션이 예외 발생 시 메모리 누수를 야기할 수 있으므로 운영 모드에서 
``PRESERVE_CONTEXT_ON_EXCEPTION``을 강제로 활성화하지 않아야 한다. 하지만, 개발 
모드에서 운영 설정에서만 발생하는 오류를 디버그하려 할 때 개발 모드로 같은 오류 보존 동작을 얻는 것은 개발하는 동안에는 유용할 수 있다. 

