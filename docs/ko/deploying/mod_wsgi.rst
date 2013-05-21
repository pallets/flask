.. _mod_wsgi-deployment:

mod_wsgi (아파치)
=================

만약 `Apache`_ 웹서브를 사용하고 있다면, `mod_wsgi`_ 를 사용할 것을 고려하라.

.. admonition:: 주의

   어플리케이션 파일에서 있을 수 있는 ``app.run()`` 호출이 ``if __name__ == '__main__':`` 블럭안에 있는지
   아니면 다른 파일로 분리되어 있는지 미리 확인해야 한다. 이것은 만약 우리가 어플리케이션을 mod_wsgi로 배포한다면
   원하지 않게 로컬 WSGI 서버를 항상 실행하기 때문에 호출되지 않음을 확인해야 한다.

.. _Apache: http://httpd.apache.org/

`mod_wsgi` 설치하기
-------------------

`mod_wsgi` 가 아직 설치되지 않았다면, 패키지 관리자를 사용하여 설치하거나, 직접 컴파일해야 한다.
mod_wsgi `installation instructions`_ 가 유닉스 시스템에서의 소스 설치를 다룬다.

만약 우분투/데비안을 사용하고 있다면 apt-get를 사용하여 다음과 같이 활성화할 수 있다:

.. sourcecode:: text

    # apt-get install libapache2-mod-wsgi

FreeBSD에에서는 `www/mod_wsgi` 포트를 컴파일하거나 pkg-add를 사용하여 `mod_wsgi` 를 설치하라:

.. sourcecode:: text

    # pkg_add -r mod_wsgi

만약 pkgsrc를 사용하고 있다면, `www/ap2-wsgi` 패키지를 컴파일하여 `mod_wsgi` 를 설치할 수 있다.

만약 처음 아파치를 리로드한 후에 세그멘테이션폴트가 나는 자식 프로세스를 발견한다면,
그것들을 무시할 수 있다. 단지 서버를 재시작하면 된다.

`.wsgi` 파일 생성하기
-----------------------

어플리케이션을 실행하기 위해서는 `yourapplication.wsgi` 파일이 필요하다.
이 파일은 application 객체를 얻기 위해 시작 시점에 `mod_wsgi`가 실행할 코드를 포함하고 있다.
그 객체는 그 파일에서 `application` 라고 불리며, application으로 사용된다.

대부분의 어플리케이션에서 다음과 같은 파일이면 충분하다::

    from yourapplication import app as application

만약 여러분이 application 객체 생성하는 팩토리 함수가 없다면, 
'application'으로 하나를 직접 임포트하여 싱글톤 객체로 사용할 수 있다.

그 파일을 나중에 다시 찾을 수 있는 어딘가에 저장하고(예:`/var/www/yourapplication`) 
`yourapplication`과 사용되는 모든 라이브러리가 파이썬 로그 경로에 있는지 확인하라.
만약 파이썬을 설치하는 것을 원하지 않으면, 시스템 전반적으로 `virtual python`_ 객체를 사용하는 것을
고려하라. 실제로 어플리케이션을 virtualenv에 설치해야 하는 것을 기억하라.
다른 방법으로는 임포트 전에 `.wsgi` 파일 내 경로를 패치하기 위한 옵션이 있다::

    import sys
    sys.path.insert(0, '/path/to/the/application')

아파치 설정하기
---------------


여러분이 해야할 마지막 일은 어플리케이션을 위한 아파치 설정 파일을 생성하는 것이다. 이 예제에서 보안적인 이유로
다른 사용자 하에서 어플리케이션을 실행하라고 'mod_wsgi'에게 말할 것이다:

.. sourcecode:: 아파치

    <VirtualHost *>
        ServerName example.com

        WSGIDaemonProcess yourapplication user=user1 group=group1 threads=5
        WSGIScriptAlias / /var/www/yourapplication/yourapplication.wsgi

        <Directory /var/www/yourapplication>
            WSGIProcessGroup yourapplication
            WSGIApplicationGroup %{GLOBAL}
            Order deny,allow
            Allow from all
        </Directory>
    </VirtualHost>

Note: WSGIDaemonProcess는 윈도우에서 구현되어 있지 않으며 아파치는 위와 같은 설정을 허용하지 않을 것이다.
윈도우 시스템에서는 해당 라인들을 제거하라:

.. sourcecode:: 아파치

	<VirtualHost *>
		ServerName example.com
		WSGIScriptAlias / C:\yourdir\yourapp.wsgi
		<Directory C:\yourdir>
			Order deny,allow
			Allow from all
		</Directory>
	</VirtualHost>
	
더 많은 정보를 위해 `mod_wsgi wiki`_를 참조하라.

.. _mod_wsgi: http://code.google.com/p/modwsgi/
.. _installation instructions: http://code.google.com/p/modwsgi/wiki/QuickInstallationGuide
.. _virtual python: http://pypi.python.org/pypi/virtualenv
.. _mod_wsgi wiki: http://code.google.com/p/modwsgi/wiki/

문제해결
--------

만약 어플리케이션이 실행되지 않는다면 아래 문제해결 가이드를 참조하라:

**문제:** 어플리케이션이 실행되지 않으며, 에러로그는 SystemExit ignored를 보여준다
    ``if __name__ == '__main__':`` 조건에 의해 보호되지 않는 어플리케이션 파일에서 ``app.run()`` 를 호출한다.
    파일에서 :meth:`~flask.Flask.run` 호출을 제거하고 `run.py` 파일로 옮기거나, if 블럭 안에 넣어라.

**문제:** 어플리케이션이 퍼미션 에러를 준다.
    아마 잘못된 사용자에 의해 어플리케이션이 실행되었을 것이다.
    어플리케이션이 접근이 필요한 폴더가 적절한 권한이 설정되어 있는지 어플리케이션이 올바른 사용자로 실행되는지 확인하라
    (`WSGIDaemonProcess` 지시어에 ``user`` 와 ``group`` 파라미터)

**문제:** 어플리케이션이 에러를 출력하며 죽는다
    mod_wsgi는 :data:`sys.stdout` 와 :data:`sys.stderr`로 어떤 것을 하는 것을 허용하지 않는다는 것을 기억라라.
    `WSGIRestrictStdout` 를 ``off``로 설정하여 이 보호를 해지할 수 있다:

    .. sourcecode:: 아파치

        WSGIRestrictStdout Off

    다른 대안으로 .wsgi 파일에서의 표준 출력을 다른 스트림으로 변환할 수 있다::

        import sys
        sys.stdout = sys.stderr

**Problem:** accessing resources gives IO errors
    Your application probably is a single .py file you symlinked into
    the site-packages folder.  Please be aware that this does not work,
    instead you either have to put the folder into the pythonpath the
    file is stored in, or convert your application into a package.

    The reason for this is that for non-installed packages, the module
    filename is used to locate the resources and for symlinks the wrong
    filename is picked up.

Support for Automatic Reloading
-------------------------------

To help deployment tools you can activate support for automatic
reloading.  Whenever something changes the `.wsgi` file, `mod_wsgi` will
reload all the daemon processes for us.

For that, just add the following directive to your `Directory` section:

.. sourcecode:: apache

   WSGIScriptReloading On

Working with Virtual Environments
---------------------------------

Virtual environments have the advantage that they never install the
required dependencies system wide so you have a better control over what
is used where.  If you want to use a virtual environment with mod_wsgi
you have to modify your `.wsgi` file slightly.

Add the following lines to the top of your `.wsgi` file::

    activate_this = '/path/to/env/bin/activate_this.py'
    execfile(activate_this, dict(__file__=activate_this))

This sets up the load paths according to the settings of the virtual
environment.  Keep in mind that the path has to be absolute.
