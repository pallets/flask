.. _fabric-deployment:

Fabric으로 전개하기
===================

`Fabric`_ Makefiles과 유사하지만 원격 서버에 있는 명령을 실행할 수 있는
기능도 갖고 있는 파이썬 도구이다.  적당한 파이썬 설치 패키지 
(:ref:`larger-applications`) 와 설정 (:ref:`config`)에 대한 좋은 개념의 결합은 
플라스크 어플리케이션을 외부 서버에 상당히 쉽게 전개하도록 해준다.

시작하기에 앞서, 우리가 사전에 빠르게 확인해야할 체크리스트가 있다:

-   Fabric 1.0 은 로컬에 설치되어 있어야한다.  이 문서는 Fabric의 
    가장 최신버전을 가정한다.
-   어플리케이션은 이미 패키지로 되어있고 동작하는 `setup.py` 파일을 
    요구한다 (:ref:`distribute-deployment`).
-   뒤따르는 예제에서 우리는 원격 서버에 `mod_wsgi` 를 사용할 것이다.
    물론 여러분이 좋아하는 서버를 사용할 수 있겠지만, 이 예제에서는
    Apache + `mod_wsgi` 를 사용하기로 했는데, 그 방식이 설치가 쉽고
    root 권한 없이도 어플리케이션을 간단하게 리로드할 수 있기 때문이다.

첫 번째 Fabfile 파일 생성하기
-----------------------------

fabfile 은 Fabric이 실행할 대상을 제어하는 것이다.  fabfile은 `fabfile.py`
라는 파일명을 갖고, `fab` 명령으로 실행된다.  그 파일에 정의된 모든 기능들은
`fab` 하위명령(subcommands)가 보여준다.  그 명령들은 하나 이상의 호스트에서
실행된다.  이 호스트들은 fabfile 파일이나 명령줄에서 정의될 수 있다.
여기에서는 fabfile 파일에 호스트들을 추가할 것이다.

아래는 현재 소스코드를 서버로 업로드하고 사전에 만들어진 가상 환경에 
설치하는 기능을 하는 기본적인 첫 번째 예제이다::

    from fabric.api import *

    # the user to use for the remote commands
    env.user = 'appuser'
    # the servers where the commands are executed
    env.hosts = ['server1.example.com', 'server2.example.com']

    def pack():
        # create a new source distribution as tarball
        local('python setup.py sdist --formats=gztar', capture=False)

    def deploy():
        # figure out the release name and version
        dist = local('python setup.py --fullname', capture=True).strip()
        # upload the source tarball to the temporary folder on the server
        put('dist/%s.tar.gz' % dist, '/tmp/yourapplication.tar.gz')
        # create a place where we can unzip the tarball, then enter
        # that directory and unzip it
        run('mkdir /tmp/yourapplication')
        with cd('/tmp/yourapplication'):
            run('tar xzf /tmp/yourapplication.tar.gz')
            # now setup the package with our virtual environment's
            # python interpreter
            run('/var/www/yourapplication/env/bin/python setup.py install')
        # now that all is set up, delete the folder again
        run('rm -rf /tmp/yourapplication /tmp/yourapplication.tar.gz')
        # and finally touch the .wsgi file so that mod_wsgi triggers
        # a reload of the application
        run('touch /var/www/yourapplication.wsgi')

위의 예제는 문서화가 잘 되고 있고 직관적일 것이다.
아래는 fabric이 제공하는 가장 일반적인 명령들을 요약했다:

-   `run` - 원격 서버에서 명령을 수행함
-   `local` - 로컬 서버에서 명령을 수행함
-   `put` - 원격 서버로 파일을 업로드함
-   `cd` - 서버에서 디렉토리를 변경함.

이 명령은 `with` 절과 결합되어 사용되어야 한다.

Fabfile 실행하기
----------------

이제 여러분은 어떻게 그 fabfile을 실행할 것인가?  `fab` 명령을 사용한다.
원격 서버에 있는 현재 버전의 코드를 전개하기 위해서 여러분은 아래 명령을 
사용할 것이다::

    $ fab pack deploy

하지만 이것은 서버에 이미 ``/var/www/yourapplication`` 폴더가 생성되어있고
``/var/www/yourapplication/env`` 을 가상 환경으로 갖고 있는 것을 요구한다.
더욱이 우리는 서버에 구성 파일이나 `.wsgi` 파일을 생성하지 않았다.  그렇다면
우리는 어떻게 신규 서버에 우리의 기반구조를 만들 수 있을까?

이것은 우리가 설치하고자 하는 서버의 개수에 달려있다.  우리가 단지
한 개의 어플리케이션 서버를 갖고 있다면 (다수의 어플리케이션들이 포함된),
fabfile 에서 명령을 생성하는 것은 과한 것이다.  그러나 명백하게 여러분은
그것을 할 수 있다.  이 경우에 여러분은 아마 그것을 `setup` 이나 `bootstrap`
으로 호출하고 그 다음에 명령줄에 명시적으로 서버명을 넣을 것이다::

    $ fab -H newserver.example.com bootstrap

신규 서버를 설치하기 위해서 여러분은 대략 다음과 같은 단계를 수행할 것이다: 

1.  ``/var/www`` 에 디렉토리 구조를 생성한다::

        $ mkdir /var/www/yourapplication
        $ cd /var/www/yourapplication
        $ virtualenv --distribute env

2.  새로운 `application.wsgi` 파일과 설정 파일 (eg: `application.cfg`) 을 
    서버로 업로드한다.

3.  `yourapplication` 에 대한 Apache 설정을 생성하고 설정을 활성화 한다.
    `.wsgi` 파일을 변경(touch)하여 어플리케이션을 자동으로 리로드하기 위해
    그 파일의 변경에 대한 감시를 활성화하는 것을 확인한다.
    ( :ref:`mod_wsgi-deployment` 에 더 많은 정보가 있다)

자 그렇다면 `application.wsgi` 파일과 `application.cfg` 파일은 어디서 왔을까?
라는 질문이 나온다.

WSGI 파일
---------

WSGI 파일은 어플리케이션이 설정파일을 어디서 찾아야 하는지 알기 위해
어플리케이션을 임포트해야하고 또한 환경 변수를 설정해야한다.  아래는 
정확히 그 설정을 하는 짧은 예제이다::

    import os
    os.environ['YOURAPPLICATION_CONFIG'] = '/var/www/yourapplication/application.cfg'
    from yourapplication import app

그리고 나서 어플리케이션 그 자체는 그 환경 변수에 대한 설정을 찾기 위해
아래와 같은 방식으로 초기화 해야한다::

    app = Flask(__name__)
    app.config.from_object('yourapplication.default_config')
    app.config.from_envvar('YOURAPPLICATION_CONFIG')

이 접근법은 이 문서의 :ref:`config` 단락에 자세히 설명되어 있다.

설정 파일
---------

위에서 언급한 것 처럼, 어플리케이션은 `YOURAPPLICATION_CONFIG` 환경 변수
를 찾음으로서 올바른 설정 파일을 찾을 것이다.  그래서 우리들은 어플리케이션이
그 변수를 찾을 수 있는 곳에 그 설정을 넣어야만 한다.  설정 파일들은 모든 
컴퓨터에서 여러 다른 상태를 갖을수 있는 불친절한 특징을 갖기 때문에 보통은 
설정 파일들을 버전화하지 않는다. 

많이 사용되는 접근법은 분리된 버전 관리 저장소에 여러 다른 서버에 대한
설정 파일들을 보관하고 모든 서버에 그것들을 받아가는(check-out) 것이다.
그리고 나서 어떤 서버에 대해 사용 중인 설정 파일은 그 파일이 심볼릭 링크로
생성되도록 기대되는 곳으로 링크를 건다 (eg: ``/var/www/yourapplication``).

다른 방법으로는, 여기에서 우리는 단지 하나 또는 두개의 서버만 가정했으므로
수동으로 그것들은 생각보다 빨리 업로드할 수 있다.

첫 번째 전개
------------

Now we can do our first deployment.  We have set up the servers so that
they have their virtual environments and activated apache configs.  Now we
can pack up the application and deploy it::

    $ fab pack deploy

Fabric will now connect to all servers and run the commands as written
down in the fabfile.  First it will execute pack so that we have our
tarball ready and then it will execute deploy and upload the source code
to all servers and install it there.  Thanks to the `setup.py` file we
will automatically pull in the required libraries into our virtual
environment.

Next Steps
----------

From that point onwards there is so much that can be done to make
deployment actually fun:

-   Create a `bootstrap` command that initializes new servers.  It could
    initialize a new virtual environment, setup apache appropriately etc.
-   Put configuration files into a separate version control repository
    and symlink the active configs into place.
-   You could also put your application code into a repository and check
    out the latest version on the server and then install.  That way you
    can also easily go back to older versions.
-   hook in testing functionality so that you can deploy to an external
    server and run the testsuite.  

Working with Fabric is fun and you will notice that it's quite magical to
type ``fab deploy`` and see your application being deployed automatically
to one or more remote servers.


.. _Fabric: http://fabfile.org/
