.. _deploying-wsgi-standalone:

독립적인 WSGI 컨테이너
======================

WSGI 어플리케이션을 포함하고 HTTP를 서비스하는 파이썬으로 개발된 인기있는 서버가 있다.
이 서버들은 실행될 때 독립적이다; 여러분은 그것들을 웹서버를 통해 프록시할 수 있다.
이와 같이 하려면 :ref:`deploying-proxy-setups` 단락을 참조하라.

Gunicorn
--------

`Gunicorn`_ 'Green Unicorn'은 UNIX를 위한 WSGI HTTP 서버이다.
이것은 루비의 Unicorn 프로젝트에서 포팅된 pre-fork worker 모델이다.
이것은 `eventlet`_와 `greenlet`_을 모두 지원한다. 
이 서버에서 플라스크 어플리케이션을 실행하는 것은 매우 간단하다::

    gunicorn myproject:app

`Gunicorn`_은 많은 커맨드라인 옵션을 제공한다 -- ``gunicorn -h`` 를 참조하라.
예를 들면 로컬호스트 4000포트로 바인딩하면서(``-b 127.0.0.1:4000``) 
4개의 worker 프로세스로 실행하기 위해서는 (``-w 4``) 아래와 같이 하면 된다::

    gunicorn -w 4 -b 127.0.0.1:4000 myproject:app

.. _Gunicorn: http://gunicorn.org/
.. _eventlet: http://eventlet.net/
.. _greenlet: http://codespeak.net/py/0.9.2/greenlet.html

Tornado
--------

`Tornado`_는 `FriendFeed`_를 강화한 확장성있는 넌블러킹 웹서버의 오픈소스 버전이다.
넌블러킹이며 epoll을 사용하기 때문에 수천개의 동시 연결을 처리할 수 있다.
이것은 이상적인 실시간 웹서비스를 의미한다. 플라스크를 이 서비스로 통합하는 것은 복잡하지 않다::

    from tornado.wsgi import WSGIContainer
    from tornado.httpserver import HTTPServer
    from tornado.ioloop import IOLoop
    from yourapplication import app

    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(5000)
    IOLoop.instance().start()


.. _Tornado: http://www.tornadoweb.org/
.. _FriendFeed: http://friendfeed.com/

Gevent
-------

`Gevent`_는 `libevent`_ 이벤트 루프 위에서 고수준 동기화 API를 제공하기 위해 `greenlet`_를 사용하는 
coroutine기반 파이썬 네트워킹 라이브러리이다::

    from gevent.wsgi import WSGIServer
    from yourapplication import app

    http_server = WSGIServer(('', 5000), app)
    http_server.serve_forever()

.. _Gevent: http://www.gevent.org/
.. _greenlet: http://codespeak.net/py/0.9.2/greenlet.html
.. _libevent: http://monkey.org/~provos/libevent/

Twisted Web
-----------

`Twisted Web`_은 `Twisted`_에 포함되어 있는 웹서버이며, 성숙된 넌블러킹 이벤트 드리븐 네트워킹 라이브러리이다.
Twisted Web은 ``twistd`` 유틸리티를 사용하여 커맨드라인을 통해 컨트롤할 수 있는 표준 WSGI 컨테이너이다::

    twistd web --wsgi myproject.app

이 예제는 ``myproject`` 모듈로부터 ``app``을 호출하는 Flask application를 실행할 것이다.

Twisted Web은 많은 플래그와 옵션을 지원하며, ``twistd`` 유틸리티 또한 많은 것을 제공한다;
더 많은 정보를 위해 ``twistd -h`` 와 ``twistd web -h``를 참조하라.
예를 들어, ``myproject`` 어플리케이션을 8080포트로  Twisted 웹서버로 서비스하려면 아래와 같이 하면 된다::

    twistd -n web --port 8080 --wsgi myproject.app

.. _Twisted: https://twistedmatrix.com/
.. _Twisted Web: https://twistedmatrix.com/trac/wiki/TwistedWeb

.. _deploying-proxy-setups:

프록시 설정
-----------

어플리케이션을 HTTP 프록시 뒤에 있는 서버들 중 하나를 사용하여 배포한다면
어플리케이션을 실행하기 위해 몇가지 헤더를 rewrite할 필요가 있을 것이다.
WSGI 환경에서 문제가 있는 두가지 값을 `REMOTE_ADDR` 와 `HTTP_HOST` 이다.
이 헤더들은 httpd에 전달하기 위한 설정을 할 수 있다. 또는 미들웨어에서 그 헤더들을 수정할 수 있다.
Werkzeug는 몇가지 설정으로 해결할 수 있는 픽서(fixer)을 포함한다. 그러나 특정한 설정을 위해 WSGI 미들웨어를
사용하기를 원할지도 모른다.

아래는 적절한 헤더를 설정하여 로컬포스트 8000번 포트로 서비스되는 어플리케이션으로 프록시하는 간단한 nginx 설정이다::

.. sourcecode:: nginx

    server {
        listen 80;

        server_name _;

        access_log  /var/log/nginx/access.log;
        error_log  /var/log/nginx/error.log;

        location / {
            proxy_pass         http://127.0.0.1:8000/;
            proxy_redirect     off;

            proxy_set_header   Host             $host;
            proxy_set_header   X-Real-IP        $remote_addr;
            proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;
        }
    }

만약 httpd가 이 헤더들을 제공하지 않는다면 가장 일반적인 설정은 `X-Forwarded-Host`로부터 호스트를 
`X-Forwarded-For`로부터 원격 어드레스를 가져오는 것이다::

    from werkzeug.contrib.fixers import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app)

.. admonition:: 헤더 신뢰

   악의저인 클라이언트에 의해 위조될 수 있는 헤더를 무조건 신뢰할 것이기 때문에 non-proxy 설정에서 
   이런 미들웨어를 사용하는 것은 보안적인 문제가 있다는 것을 기억하라.
   
만약 다른 헤더로부터 헤더들은 rewrite하려면, 아래와 같이 픽서를 사용할 수 있다::

    class CustomProxyFix(object):

        def __init__(self, app):
            self.app = app

        def __call__(self, environ, start_response):
            host = environ.get('HTTP_X_FHOST', '')
            if host:
                environ['HTTP_HOST'] = host
            return self.app(environ, start_response)

    app.wsgi_app = CustomProxyFix(app.wsgi_app)
