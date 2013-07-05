.. _deploying-fastcgi:

FastCGI
=======

FastCGI는 `nginx`_, `lighttpd`_, `cherokee`_ 와 같은 서버에서 사용할 수 있는 배포 옵션이다;
다른 옵션을 보려면 :ref:`deploying-uwsgi` 와 :ref:`deploying-wsgi-standalone` 를 확인하라.
WSGI 어플리케이션을 사용하기 위해서는 먼저 FastCGI 서버가 필요하다. 가장 인기있는 것은 `flup`_이며,
설명을 위해 사용할 것이다. 아래와 같이 설치되어 있는지 확인하라.

.. admonition:: 주의

   어플리케이션 파일에서 있을 수 있는 ``app.run()`` 호출이 ``if __name__ == '__main__':`` 블럭안에 있는지
   아니면 다른 파일로 분리되어 있는지 미리 확인해야 한다. 이것은 만약 우리가 어플리케이션을 FastCGI로 배포한다면
   원하지 않게 로컬 WSGI 서버를 항상 실행하기 때문에 호출되지 않음을 확인해야 한다.

`.fcgi` 파일 생성하기
-----------------------

먼저 FastCGI 서버 파일을 만드는 것이 필요하다. 그것을 `yourapplication.fcgi`:: 이라고 부르자.

    #!/usr/bin/python
    from flup.server.fcgi import WSGIServer
    from yourapplication import app

    if __name__ == '__main__':
        WSGIServer(app).run()

이것은 아파치에 적용하기에는 충분하지만 nginx나 lighttpd의 오래된 버전의 경우 FastCGI 서버와ㅏ 통신하기 위해 
명시적으로 소켓을 전달해야 한다. :class:`~flup.server.fcgi.WSGIServer`::에 소켓 경로를 전달해야 한다.

    WSGIServer(application, bindAddress='/path/to/fcgi.sock').run()

그 경로는 서버 설정에 정의된 것과 정확히 같아야 한다.

`yourapplication.fcgi`을 다시 찾을 수 있는 어딘가에 저장하라.
`/var/www/yourapplication` 나 비슷한 곳에 두면 된다.

서버가 이 파일을 실행할 수 있도록 실행 가능 비트를 설정하라:

.. sourcecode:: text

    # chmod +x /var/www/yourapplication/yourapplication.fcgi

아파치 설정하기
------------------

기본적인 아파치 배포는 위 예제로 충분하나, `.fcgi` 파일이 example.com/yourapplication.fcgi/news/ 와 같이
어플리케이션 URL에 보일 것이다. URL에 yourapplication.fcgi을 보이지 않게 하는 며가지 설정 방법이 있다.
가장 많이 사용되는 방법은 ScriptAlias 설정 지시어를 사용하는 것이다:

    <VirtualHost *>
        ServerName example.com
        ScriptAlias / /path/to/yourapplication.fcgi/
    </VirtualHost>

만약 공유된 웹호스트에서와 같이 ScriptAlias를 설정할 수 없다면,
URL에서 yourapplication.fcgi를 제거하기 위해 WSGI 미들웨어를 사용할 수 있다.
.htaccess:: 를 설정하라.

    <IfModule mod_fcgid.c>
       AddHandler fcgid-script .fcgi
       <Files ~ (\.fcgi)>
           SetHandler fcgid-script
           Options +FollowSymLinks +ExecCGI
       </Files>
    </IfModule>

    <IfModule mod_rewrite.c>
       Options +FollowSymlinks
       RewriteEngine On
       RewriteBase /
       RewriteCond %{REQUEST_FILENAME} !-f
       RewriteRule ^(.*)$ yourapplication.fcgi/$1 [QSA,L]
    </IfModule>

yourapplication.fcgi:: 를 설정하라.

    #!/usr/bin/python
    #: optional path to your local python site-packages folder
    import sys
    sys.path.insert(0, '<your_local_path>/lib/python2.6/site-packages')

    from flup.server.fcgi import WSGIServer
    from yourapplication import app

    class ScriptNameStripper(object):
       def __init__(self, app):
           self.app = app

       def __call__(self, environ, start_response):
           environ['SCRIPT_NAME'] = ''
           return self.app(environ, start_response)

    app = ScriptNameStripper(app)

    if __name__ == '__main__':
        WSGIServer(app).run()

lighttpd 설정하기
--------------------

lighttpd를 위한 기본적인 FastCGI 설정은 아래와 같다::

    fastcgi.server = ("/yourapplication.fcgi" =>
        ((
            "socket" => "/tmp/yourapplication-fcgi.sock",
            "bin-path" => "/var/www/yourapplication/yourapplication.fcgi",
            "check-local" => "disable",
            "max-procs" => 1
        ))
    )

    alias.url = (
        "/static/" => "/path/to/your/static"
    )

    url.rewrite-once = (
        "^(/static($|/.*))$" => "$1",
        "^(/.*)$" => "/yourapplication.fcgi$1"

FastCGI, alias, rewrite modules 모듈을 활성화하는 것을 기억하라.
이 설정은 어플리케이션을 `/yourapplication`에 바인드한다.
만약 어플리케이션을 URL 루트에서 실행하기를 원한다면, :class:`~werkzeug.contrib.fixers.LighttpdCGIRootFix` 미들웨어 관련
lighttpd 버그의 회피 수단을 적용해야 한다.

어플리케이션을 URL 루트에 마운트하는 경우에만 이것을 적용해야 한다.
또한 `FastCGI and Python <http://redmine.lighttpd.net/wiki/lighttpd/Docs:ModFastCGI>`_ 에 대한 더 많은 정보를 위해 
lighttpd 문서를 확인하라.(명시적으로 소켓을 전달하는 것이 더 이상 필요하지 않음을 주목하라.)

nginx 설정하기
-----------------

nginx에 FastCGI 어플리케이션 설치는 기본적으로 어떠한 FastCGI 파라미터가 전달되지 않기 때문에 조금 다르다.

nginx를 위한 기본적인 플라스크 FastCGI 설정은 아래와 같다:: 

    location = /yourapplication { rewrite ^ /yourapplication/ last; }
    location /yourapplication { try_files $uri @yourapplication; }
    location @yourapplication {
        include fastcgi_params;
        fastcgi_split_path_info ^(/yourapplication)(.*)$;
        fastcgi_param PATH_INFO $fastcgi_path_info;
        fastcgi_param SCRIPT_NAME $fastcgi_script_name;
        fastcgi_pass unix:/tmp/yourapplication-fcgi.sock;
    }

이 설정은 어플리케이션을 `/yourapplication`에 바인드한다.
URL 루트에 어플리케이션을 두길 원한다면, `PATH_INFO` 와 `SCRIPT_NAME`를 계산하는 방법을
이해할 필요가 없기 때문에 조금 더 간단하다::

    location / { try_files $uri @yourapplication; }
    location @yourapplication {
        include fastcgi_params;
        fastcgi_param PATH_INFO $fastcgi_script_name;
        fastcgi_param SCRIPT_NAME "";
        fastcgi_pass unix:/tmp/yourapplication-fcgi.sock;
    }

FastCGI 프로세스 실행하기
-------------------------

Nginx와 다른 서버들은 FastCGI 어플리케이션을 로드하지 않기 때문에, 스스로 로드를 해야 한다.
`관리자가 FastCGI 프로세스를 관리할 수 있다. <http://supervisord.org/configuration.html#fcgi-program-x-section-settings>`_
다른 FastCGI 프로세스 관리자를 찾아 보거나, 부팅할 때 `.fcgi` 파일을 실행하도록 스크립트를 작성할 수 있다.
(예. SysV ``init.d`` 스크립트를 사용)
임시 방편으로는 GNU 화면 안에서 항상 ``.fcgi`` 스크립트를 실행할 수 있다.
상세를 위해 ``man screen`` 를 확인하고, 이것이 시스템을 재시작하면 지속되지 않는 수동적인 해결책임을 주의하라::

    $ screen
    $ /var/www/yourapplication/yourapplication.fcgi

디버깅
---------

FastCGI 배포는 대부분 웹서버에서 디버깅하기 어려운 경향이 있다.
아주 종종 서버 로그가 알려는 유일한 정보는 "premature end of headers" 라인과 함께 나타난다.
어플리케이션을 디버깅하기 위해서, 여러분에게 정말로 줄 수 있는 유일한 방법은
정확한 사용자로 바꾸고 손으로 직접 어플리케이션을 실행하는 것이다. 

아래 예제는 어플리케이션을 `application.fcgi` 라고 부르고, 웹서버가 사용자가 `www-data`라고 가정한다::

    $ su www-data
    $ cd /var/www/yourapplication
    $ python application.fcgi
    Traceback (most recent call last):
      File "yourapplication.fcgi", line 4, in <module>
    ImportError: No module named yourapplication

이 경우 에러는 "yourapplication"가 파이썬 경로에 없는 것 같이 보인다. 일반적인 문제는 아래와 같다::

-   상대 경로가 사용된 경우. 현재 작업 디렉토리에 의존하지 마라.
-   웹서버에 의해 설정되지 않는 환경 변수에 의존적인 코드.
-   다른 파이썬 해석기가 사용된 경우.

.. _nginx: http://nginx.org/
.. _lighttpd: http://www.lighttpd.net/
.. _cherokee: http://www.cherokee-project.com/
.. _flup: http://trac.saddi.com/flup
