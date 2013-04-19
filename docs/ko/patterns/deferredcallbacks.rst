.. _deferred-callbacks:

지연된(deferred) 요청 콜백
==========================

플라스크의 설계 원칙 중 한가지는 응답 객체가 생성되고 그 객체를 수정하거나
대체할 수 있는 잠재적인 콜백의 호출 사슬로 그 객체를 전달하는 것이다.
요청 처리가 시작될 때, 아직은 응답 객체를 존재하지 않는다.  뷰 함수나
시스템에 있는 어떤 다른 컴포넌트에 의해 필요할 때 생성된다.

하지만 응답이 아직 존재하지 않는 시점에서 응답을 수정하려 하면 어떻게 되는가?
그에 대한 일반적인 예제는 응답 객체에 있는 쿠키를 설정하기를 원하는
before-request 함수에서 발생할 것이다.

한가지 방법은 그런 상황을 피하는 것이다. 꽤 자주 이렇게 하는게 가능하다.
예를 들면 여러분은 그런 로직을 after-request 콜백으로 대신 옮기도록 
시도할 수 있다.  하지만 때때로 거기에 있는 코드를 옮기는 것은 유쾌한 
일이 아니거나 코드가 대단히 부자연스럽게 보이게 된다.

다른 가능성으로서 여러분은 :data:`~flask.g` 객체에 여러 콜백 함수를
추가하고 요청의 끝부분에서 그것을 호출할 수 있다.  이 방식으로 여러분은
어플리케이션의 어느 위치로도 코드 실행을 지연시킬 수 있다.


데코레이터
----------

다음에 나올 데코레이터가 핵심이다. 그 데코레이터는 :data:`~flask.g` 객체에
있는 리스트에 함수를 등록한다::

    from flask import g

    def after_this_request(f):
        if not hasattr(g, 'after_request_callbacks'):
            g.after_request_callbacks = []
        g.after_request_callbacks.append(f)
        return f


Calling the Deferred
--------------------

Now you can use the `after_this_request` decorator to mark a function to
be called at the end of the request.  But we still need to call them.  For
this the following function needs to be registered as
:meth:`~flask.Flask.after_request` callback::

    @app.after_request
    def call_after_request_callbacks(response):
        for callback in getattr(g, 'after_request_callbacks', ()):
            response = callback(response)
        return response


A Practical Example
-------------------

Now we can easily at any point in time register a function to be called at
the end of this particular request.  For example you can remember the
current language of the user in a cookie in the before-request function::

    from flask import request

    @app.before_request
    def detect_user_language():
        language = request.cookies.get('user_lang')
        if language is None:
            language = guess_language_from_request()
            @after_this_request
            def remember_language(response):
                response.set_cookie('user_lang', language)
        g.language = language
