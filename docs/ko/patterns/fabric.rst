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

Running Fabfiles
----------------

Now how do you execute that fabfile?  You use the `fab` command.  To
deploy the current version of the code on the remote server you would use
this command::

    $ fab pack deploy

However this requires that our server already has the
``/var/www/yourapplication`` folder created and
``/var/www/yourapplication/env`` to be a virtual environment.  Furthermore
are we not creating the configuration or `.wsgi` file on the server.  So
how do we bootstrap a new server into our infrastructure?

This now depends on the number of servers we want to set up.  If we just
have one application server (which the majority of applications will
have), creating a command in the fabfile for this is overkill.  But
obviously you can do that.  In that case you would probably call it
`setup` or `bootstrap` and then pass the servername explicitly on the
command line::

    $ fab -H newserver.example.com bootstrap

To setup a new server you would roughly do these steps:

1.  Create the directory structure in ``/var/www``::

        $ mkdir /var/www/yourapplication
        $ cd /var/www/yourapplication
        $ virtualenv --distribute env

2.  Upload a new `application.wsgi` file to the server and the
    configuration file for the application (eg: `application.cfg`)

3.  Create a new Apache config for `yourapplication` and activate it.
    Make sure to activate watching for changes of the `.wsgi` file so
    that we can automatically reload the application by touching it.
    (See :ref:`mod_wsgi-deployment` for more information)

So now the question is, where do the `application.wsgi` and
`application.cfg` files come from?

The WSGI File
-------------

The WSGI file has to import the application and also to set an environment
variable so that the application knows where to look for the config.  This
is a short example that does exactly that::

    import os
    os.environ['YOURAPPLICATION_CONFIG'] = '/var/www/yourapplication/application.cfg'
    from yourapplication import app

The application itself then has to initialize itself like this to look for
the config at that environment variable::

    app = Flask(__name__)
    app.config.from_object('yourapplication.default_config')
    app.config.from_envvar('YOURAPPLICATION_CONFIG')

This approach is explained in detail in the :ref:`config` section of the
documentation.

The Configuration File
----------------------

Now as mentioned above, the application will find the correct
configuration file by looking up the `YOURAPPLICATION_CONFIG` environment
variable.  So we have to put the configuration in a place where the
application will able to find it.  Configuration files have the unfriendly
quality of being different on all computers, so you do not version them
usually.

A popular approach is to store configuration files for different servers
in a separate version control repository and check them out on all
servers.  Then symlink the file that is active for the server into the
location where it's expected (eg: ``/var/www/yourapplication``).

Either way, in our case here we only expect one or two servers and we can
upload them ahead of time by hand.

First Deployment
----------------

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
