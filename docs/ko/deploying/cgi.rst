CGI
===

다른 모든 배포 방법을 적용할 수 없다면, CGI는 확실히 가능할 것이다.
CGI는 거의 모든 주요 서버에 의해 제공되지만 보통 차선의 성능을 가진다.

또한 CGI와 같은 환경에서 실행할 수 있는 구글의 `App Engine`_ 에서 플라스크 어플리케이션을 사용할 수 있는 방법이기도 하다.

.. admonition:: 주의

   어플리케이션 파일에서 있을 수 있는 ``app.run()`` 호출이 ``if __name__ == '__main__':`` 블럭안에 있는지
   아니면 다른 파일로 분리되어 있는지 미리 확인해야 한다. 이것은 만약 우리가 어플리케이션을 CGI/앱엔진으로 배포한다면
   원하지 않게 로컬 WSGI 서버를 항상 실행하기 때문에 호출되지 않음을 확인해야 한다.

`.cgi` 파일 만들기
----------------------

먼저 CGI 어플리케이션 파일을 만드는 것이 필요하다. 그것을 `yourapplication.cgi`:: 이라고 부르자.

    #!/usr/bin/python
    from wsgiref.handlers import CGIHandler
    from yourapplication import app

    CGIHandler().run(app)

서버 설정
------------

보통 서버를 설정하는 두가지 방법이 있다.
`.cgi` 를 `cgi-bin` 으로 복사하거나(`mod_rewrite` 나 URL을 재작성하는 유사한 것을 사용)
서버 지점을 파일에 직접 작성한다.

아파치의 경우, 아래와 같이 설정 파일 안에 입력할 수 있다:

.. sourcecode:: apache

    ScriptAlias /app /path/to/the/application.cgi

그러나 공유된 웹호스팅에서는 아파치 설정에 접근할 수 없을 지도 모른다.
이런 경우, 여러분의 어플리케이션이 실행되기를 원하는 공개 디렉토리에 있는 `.htaccess` 파일에 
입력할 수 있으나, 이 경우엔는 `ScriptAlias` 지시어는 적용되지 않을 것이다:

.. sourcecode:: apache
    
    RewriteEngine On
    RewriteCond %{REQUEST_FILENAME} !-f # Don't interfere with static files
    RewriteRule ^(.*)$ /path/to/the/application.cgi/$1 [L]

더 많으 정보를 위해 사용하는 웹서버의 문서를 참조하라.

.. _App Engine: http://code.google.com/appengine/
