HTTP 메소드 오버라이드 추가하기
===============================

어떤 HTTP 프록시는 임시적인 HTTP 메소드나 새로운 HTTP 메소드 (PATCH 같은)
를 지원하지 않는다.  그런 경우에 프로토콜 전체를 위반하는 방식으로 
HTTP 메소드를 다른 HTTP 메소드로 "프록시" 하는 것이 가능하다.

이렇게 동작하는 방식은 클라이언트가 HTTP POST로 요청하고 
``X-HTTP-Method-Override`` 헤더를 설정하고 그 값으로 의도하는 HTTP 메소드
(``PATCH`` 와 같은)를 설정하면 된다.

이것은 HTTP 미들웨어로 쉽게 수행할 수 있다::

    class HTTPMethodOverrideMiddleware(object):
        allowed_methods = frozenset([
            'GET',
            'HEAD',
            'POST',
            'DELETE',
            'PUT',
            'PATCH',
            'OPTIONS'
        ])
        bodyless_methods = frozenset(['GET', 'HEAD', 'OPTIONS', 'DELETE'])

        def __init__(self, app):
            self.app = app

        def __call__(self, environ, start_response):
            method = environ.get('HTTP_X_HTTP_METHOD_OVERRIDE', '').upper()
            if method in self.allowed_methods:
                method = method.encode('ascii', 'replace')
                environ['REQUEST_METHOD'] = method
            if method in self.bodyless_methods:
                environ['CONTENT_LENGTH'] = '0'
            return self.app(environ, start_response)

플라스크로 이것을 하려면 아래와 같이 하면 된다::

    from flask import Flask

    app = Flask(__name__)
    app.wsgi_app = HTTPMethodOverrideMiddleware(app.wsgi_app)
