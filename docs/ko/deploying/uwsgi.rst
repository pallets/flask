.. _deploying-uwsgi:

uWSGI
=====

uWSGI는 `nginx`_, `lighttpd`_, `cherokee`_ 와 같은 서버에서 사용할 수 있는 배포 옵션이다;
다른 옵션을 보려면 :ref:`deploying-fastcgi` 와 :ref:`deploying-wsgi-standalone` 를 확인하라.
uWSGI 프로토토콜로 WSGI 어플리케이션을 사용하기 위해서는 먼저 uWSGI 서버가 필요하다. uWSGI는프로토콜이면서 어플리케이션 서버이다;
어플리케이션서버는 uWSGI, FastCGI,  HTTP 프로토콜을 서비스할 수 있다.

가장 인기있는 uWSGI 서버는 `uwsgi`_이며,
설명을 위해 사용할 것이다. 아래와 같이 설치되어 있는지 확인하라.

.. admonition:: 주의

   어플리케이션 파일에서 있을 수 있는 ``app.run()`` 호출이 ``if __name__ == '__main__':`` 블럭안에 있는지
   아니면 다른 파일로 분리되어 있는지 미리 확인해야 한다. 이것은 만약 우리가 어플리케이션을 uWSGI로 배포한다면
   원하지 않게 로컬 WSGI 서버를 항상 실행하기 때문에 호출되지 않음을 확인해야 한다.

uwsgi로 app 시작하기
--------------------

`uwsgi`는 파이썬 모듈에 있는 WSGI callables에서 운영하기 위해 설계되어 있다.

myapp.py에 flask application이 있다면 아래와 같이 사용하라:

.. sourcecode:: text

    $ uwsgi -s /tmp/uwsgi.sock --module myapp --callable app

또는 아래와 같은 방법도 사용할 수 있다:

.. sourcecode:: text

    $ uwsgi -s /tmp/uwsgi.sock -w myapp:app

nginx 설정하기
--------------

nginx를 위한 기본적인 flask uWSGI 설정은 아래와 같다::

    location = /yourapplication { rewrite ^ /yourapplication/; }
    location /yourapplication { try_files $uri @yourapplication; }
    location @yourapplication {
      include uwsgi_params;
      uwsgi_param SCRIPT_NAME /yourapplication;
      uwsgi_modifier1 30;
      uwsgi_pass unix:/tmp/uwsgi.sock;
    }

이 설정은 어플리케이션을 `/yourapplication`에 바인드한다.
URL 루트에 어플리케이션을 두길 원한다면, WSGI `SCRIPT_NAME`를 알려줄 필요가 없거나
uwsgi modifier를 설정할 필요가 없기 때문에 조금 더 간단하다::

This configuration binds the application to `/yourapplication`.  If you want
to have it in the URL root it's a bit simpler because you don't have to tell
it the WSGI `SCRIPT_NAME` or set the uwsgi modifier to make use of it::

    location / { try_files $uri @yourapplication; }
    location @yourapplication {
        include uwsgi_params;
        uwsgi_pass unix:/tmp/uwsgi.sock;
    }

.. _nginx: http://nginx.org/
.. _lighttpd: http://www.lighttpd.net/
.. _cherokee: http://www.cherokee-project.com/
.. _uwsgi: http://projects.unbit.it/uwsgi/
