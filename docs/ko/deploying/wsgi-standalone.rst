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

Proxy Setups
------------

If you deploy your application using one of these servers behind an HTTP proxy
you will need to rewrite a few headers in order for the application to work.
The two problematic values in the WSGI environment usually are `REMOTE_ADDR`
and `HTTP_HOST`.  You can configure your httpd to pass these headers, or you
can fix them in middleware.  Werkzeug ships a fixer that will solve some common
setups, but you might want to write your own WSGI middleware for specific
setups.

Here's a simple nginx configuration which proxies to an application served on
localhost at port 8000, setting appropriate headers:

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

If your httpd is not providing these headers, the most common setup invokes the
host being set from `X-Forwarded-Host` and the remote address from
`X-Forwarded-For`::

    from werkzeug.contrib.fixers import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app)

.. admonition:: Trusting Headers

   Please keep in mind that it is a security issue to use such a middleware in
   a non-proxy setup because it will blindly trust the incoming headers which
   might be forged by malicious clients.

If you want to rewrite the headers from another header, you might want to
use a fixer like this::

    class CustomProxyFix(object):

        def __init__(self, app):
            self.app = app

        def __call__(self, environ, start_response):
            host = environ.get('HTTP_X_FHOST', '')
            if host:
                environ['HTTP_HOST'] = host
            return self.app(environ, start_response)

    app.wsgi_app = CustomProxyFix(app.wsgi_app)
