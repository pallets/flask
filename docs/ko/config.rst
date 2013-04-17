.. _config:

설정 다루기
======================

.. versionadded:: 0.3

어플리케이션들은 일종의 설정 및 구성을 필요로 한다. 어플리케이션 실행 환경에서 다양한 
종류의 설정 값들을 변경 할 수 있다. 디버깅모드를 변경하거나 비밀 키(secret key)를 
설정하거나그밖의 다른 환경에 관련된 값을 변경시킬 수 있다.

Flask는 일반적인 경우 어플리케이션이 구동될때에 설정값들을 사용될 수 있어야
하도록 설계되었다. 설정값들을 하드코드(hard code)로 적용 할 수도 있는데 이 방식은
작은 규모의 어프리케이션에서는 그리 나쁘지 않은 방법이지만 더 나은 방법들이 있다.


설정값을 독립적으로 로드하는 방법으로, 이미 로드된 설정들값들 중에 속해 있는
설정 객체(config object)를 사용할 수 있다:
:class:`~flask.Flask` 객체의 :attr:`~flask.Flask.config` 속성을 참고.
이 객체의 속성을 통해 Flask 자신의 특정 설정값을 저장할수 있고 Flask의
확장 플러그인들도 자신의 설정값을 저장할 수 있다.
마찬가지로, 여러분의 어플리키에션 성정값 역시 저장할 수 있다.


설정 기초연습
--------------------

:attr:`~flask.Flask.config` 은 실제로는 dictionary 의 서브클래스이며,
다른 dictionary 처럼 다음과 같이 수정될 수 있다::

    app = Flask(__name__)
    app.config['DEBUG'] = True

확정된 설정값들은 또한 :attr:`~flask.Flask` 객체로 전달될 수 있으며,
그 객체를 통해 설정값들을 읽거나 쓸수 있다. ::

    app.debug = True

한번에 다수의 키(key)들을 업데이트 하기 위해서는 :meth:`dict.update` 
함수를 사용 할 수 있다. ::

    app.config.update(
        DEBUG=True,
        SECRET_KEY='...'
    )


내장된 고유 설정값들
----------------------------

다음의 설정값들은 Flask 의 내부에서 이미 사용되고 있는 것들이다. :

.. tabularcolumns:: |p{6.5cm}|p{8.5cm}|

================================= =========================================
``DEBUG``                         디버그 모드를 활성화/비활성화 함
``TESTING``                       테스팅 모드를 활성화/비활성화 함
``PROPAGATE_EXCEPTIONS``          명시적으로 예외를 전파하는 것에 대한 
                                  활성화 혹은 비활성화 함.
                                  이 값을 특별히 설정을 안하거나 
                                  명시적으로 `None` 으로 설정했을 경우라도 
                                  `TESTING` 혹은 `DEBUG` 가 true 라면 이 값
                                  역시 true 가 된다.
``PRESERVE_CONTEXT_ON_EXCEPTION`` 어플리케이션이 디버그모드에 있는 경우 
                                  요청 컨텍스트는 디버거에서 데이터를 확인
                                  하기 위해 예외를 발생시키지 않는다.
                                  이 설정을 이 키값을 설정하여 이 설정을
                                  비활성화 할 수 있다. 또한 이 설정은 
                                  제품화된(하지만 매우 위험 할 수 있는) 
                                  어플리케이션을 디버깅하기위해 유리 할수 
                                  있으며 디버거 실행을 위해 강제로 
                                  사용하도록 설정하고 싶을 때 사용가능하다.
``SECRET_KEY``                    비밀키
``SESSION_COOKIE_NAME``           세션 쿠키의 이름
``SESSION_COOKIE_DOMAIN``         세션 쿠키에 대한 도메인.
                                  이값이 설정되어 있지 않은 경우 쿠키는
                                  ``SERVER_NAME`` 의 모든 하위 도메인에 
                                  대하여 유효하다.
``SESSION_COOKIE_PATH``           세션 쿠키에 대한 경로를 설정한다.  
                                  이값이 설정되어 있지 않은 경우 쿠키는
                                  ``'/'`` 로 설정되어 있지 않은 모든
                                  ``APPLICATION_ROOT`` 에 대해서 유효하다
``SESSION_COOKIE_HTTPONLY``       쿠키가 httponly 플래그를 설정해야만 
                                  하도록 통제한다.
                                  기본값은 `True` 이다.
``SESSION_COOKIE_SECURE``         쿠키가 secure 플래그를 설정해야만 
                                  하도록 통제한다. 기본값은 `False` 이다.
``PERMANENT_SESSION_LIFETIME``    :class:`datetime.timedelta` 를 이용하여 
                                  영구 세션 유지 시간을 설정한다.
                                  Flask 0.8버전부터 integer 타입의 초단위로
                                  설정이 가능하다.
``USE_X_SENDFILE``                x-sendfile 기능을 활성화/비활성화 함
``LOGGER_NAME``                   로거의 이름을 설정함
``SERVER_NAME``                   서버의 이름과 포트 번호를 뜻한다.
                                  서브도메인을 지원하기 위해 요구된다. (예:
                                  ``'myapp.dev:5000'``)  
                                  이 값을 “localhost” 로 설정하는 것은 서브
                                  도메인을 지원하지 않는 것에 그리 도움이
                                  되지는 않는다는 것을 주의하자.
                                  또한 ``SERVER_NAME`` 를 설정하는 것은
                                  기본적으로 요청 컨텍스트 없이 어플리케이션
                                  컨텍스트를 통해 URL을 생성 할 수 있도록 
                                  해준다.
``APPLICATION_ROOT``              어플리케이션이 전체 도메인을 사용하지 
                                  않거나 서브도메인을 사용하지 않는 경우
                                  이 값은 어플리케이션이 어느 경로에서 
                                  실행되기 위해 설정되어 있는지 결정한다.
                                  이값은 세션 쿠키에서 경로 값으로 사용된다
                                  만약 도메인이 사용되는 경우 이 값은 
                                  ``None`` 이다.
``MAX_CONTENT_LENGTH``            만약 이 변수 값이 바이트수로 설정되면, 들어오는 
                                  요청에 대해서 이 값보다 더 큰 길이의 컨텐트일 경우 
                                  413 상태 코드를 리턴한다.
``SEND_FILE_MAX_AGE_DEFAULT``:    :meth:`~flask.Flask.send_static_file` (기본 정적파일 핸들러)
                                  와 :func:`~flask.send_file` 에서 사용하는 캐시 제어에 대한 
                                  최대 시간은 초단위로 정한다. 파일 단위로 사용되는 이 값을 
                                  덮어쓰기 위해서는 :class:`~flask.Flask` 나 :class:`~flask.Blueprint` 를 
                                  개별적으로 후킹하여 :meth:`~flask.Flask.get_send_file_max_age`를 사용한다.
                                  기본값은 43200초 이다(12 시간).
``TRAP_HTTP_EXCEPTIONS``          만약 이 값이 ``True`` 로 셋팅되어 있다면 Flask는 
                                  HTTP 예외처리를 위한 에러 핸들러를 실행 하지 않는다.
                                  but instead treat the
                                  exception like any other and bubble it
                                  through the exception stack.  This is
                                  helpful for hairy debugging situations
                                  where you have to find out where an HTTP
                                  exception is coming from.
``TRAP_BAD_REQUEST_ERRORS``       Werkzeug's internal data structures that
                                  deal with request specific data will
                                  raise special key errors that are also
                                  bad request exceptions.  Likewise many
                                  operations can implicitly fail with a
                                  BadRequest exception for consistency.
                                  Since it's nice for debugging to know
                                  why exactly it failed this flag can be
                                  used to debug those situations.  If this
                                  config is set to ``True`` you will get
                                  a regular traceback instead.
``PREFERRED_URL_SCHEME``          The URL scheme that should be used for
                                  URL generation if no URL scheme is
                                  available.  This defaults to ``http``.
``JSON_AS_ASCII``                 By default Flask serialize object to
                                  ascii-encoded JSON.  If this is set to
                                  ``False`` Flask will not encode to ASCII
                                  and output strings as-is and return
                                  unicode strings.  ``jsonfiy`` will
                                  automatically encode it in ``utf-8``
                                  then for transport for instance.
================================= =========================================

.. admonition:: More on ``SERVER_NAME``

   The ``SERVER_NAME`` key is used for the subdomain support.  Because
   Flask cannot guess the subdomain part without the knowledge of the
   actual server name, this is required if you want to work with
   subdomains.  This is also used for the session cookie.

   Please keep in mind that not only Flask has the problem of not knowing
   what subdomains are, your web browser does as well.  Most modern web
   browsers will not allow cross-subdomain cookies to be set on a
   server name without dots in it.  So if your server name is
   ``'localhost'`` you will not be able to set a cookie for
   ``'localhost'`` and every subdomain of it.  Please chose a different
   server name in that case, like ``'myapplication.local'`` and add
   this name + the subdomains you want to use into your host config
   or setup a local `bind`_.

.. _bind: https://www.isc.org/software/bind

.. versionadded:: 0.4
   ``LOGGER_NAME``

.. versionadded:: 0.5
   ``SERVER_NAME``

.. versionadded:: 0.6
   ``MAX_CONTENT_LENGTH``

.. versionadded:: 0.7
   ``PROPAGATE_EXCEPTIONS``, ``PRESERVE_CONTEXT_ON_EXCEPTION``

.. versionadded:: 0.8
   ``TRAP_BAD_REQUEST_ERRORS``, ``TRAP_HTTP_EXCEPTIONS``,
   ``APPLICATION_ROOT``, ``SESSION_COOKIE_DOMAIN``,
   ``SESSION_COOKIE_PATH``, ``SESSION_COOKIE_HTTPONLY``,
   ``SESSION_COOKIE_SECURE``

.. versionadded:: 0.9
   ``PREFERRED_URL_SCHEME``

.. versionadded:: 0.10
   ``JSON_AS_ASCII``

Configuring from Files
----------------------

Configuration becomes more useful if you can store it in a separate file,
ideally located outside the actual application package. This makes
packaging and distributing your application possible via various package
handling tools (:ref:`distribute-deployment`) and finally modifying the
configuration file afterwards.

So a common pattern is this::

    app = Flask(__name__)
    app.config.from_object('yourapplication.default_settings')
    app.config.from_envvar('YOURAPPLICATION_SETTINGS')

This first loads the configuration from the
`yourapplication.default_settings` module and then overrides the values
with the contents of the file the :envvar:`YOURAPPLICATION_SETTINGS`
environment variable points to.  This environment variable can be set on
Linux or OS X with the export command in the shell before starting the
server::

    $ export YOURAPPLICATION_SETTINGS=/path/to/settings.cfg
    $ python run-app.py
     * Running on http://127.0.0.1:5000/
     * Restarting with reloader...

On Windows systems use the `set` builtin instead::

    >set YOURAPPLICATION_SETTINGS=\path\to\settings.cfg

The configuration files themselves are actual Python files.  Only values
in uppercase are actually stored in the config object later on.  So make
sure to use uppercase letters for your config keys.

Here is an example of a configuration file::

    # Example configuration
    DEBUG = False
    SECRET_KEY = '?\xbf,\xb4\x8d\xa3"<\x9c\xb0@\x0f5\xab,w\xee\x8d$0\x13\x8b83'

Make sure to load the configuration very early on, so that extensions have
the ability to access the configuration when starting up.  There are other
methods on the config object as well to load from individual files.  For a
complete reference, read the :class:`~flask.Config` object's
documentation.


Configuration Best Practices
----------------------------

The downside with the approach mentioned earlier is that it makes testing
a little harder.  There is no single 100% solution for this problem in
general, but there are a couple of things you can keep in mind to improve
that experience:

1.  create your application in a function and register blueprints on it.
    That way you can create multiple instances of your application with
    different configurations attached which makes unittesting a lot
    easier.  You can use this to pass in configuration as needed.

2.  Do not write code that needs the configuration at import time.  If you
    limit yourself to request-only accesses to the configuration you can
    reconfigure the object later on as needed.


Development / Production
------------------------

Most applications need more than one configuration.  There should be at
least separate configurations for the production server and the one used
during development.  The easiest way to handle this is to use a default
configuration that is always loaded and part of the version control, and a
separate configuration that overrides the values as necessary as mentioned
in the example above::

    app = Flask(__name__)
    app.config.from_object('yourapplication.default_settings')
    app.config.from_envvar('YOURAPPLICATION_SETTINGS')

Then you just have to add a separate `config.py` file and export
``YOURAPPLICATION_SETTINGS=/path/to/config.py`` and you are done.  However
there are alternative ways as well.  For example you could use imports or
subclassing.

What is very popular in the Django world is to make the import explicit in
the config file by adding an ``from yourapplication.default_settings
import *`` to the top of the file and then overriding the changes by hand.
You could also inspect an environment variable like
``YOURAPPLICATION_MODE`` and set that to `production`, `development` etc
and import different hardcoded files based on that.

An interesting pattern is also to use classes and inheritance for
configuration::

    class Config(object):
        DEBUG = False
        TESTING = False
        DATABASE_URI = 'sqlite://:memory:'

    class ProductionConfig(Config):
        DATABASE_URI = 'mysql://user@localhost/foo'

    class DevelopmentConfig(Config):
        DEBUG = True

    class TestingConfig(Config):
        TESTING = True

To enable such a config you just have to call into
:meth:`~flask.Config.from_object`::

    app.config.from_object('configmodule.ProductionConfig')

There are many different ways and it's up to you how you want to manage
your configuration files.  However here a list of good recommendations:

-   keep a default configuration in version control.  Either populate the
    config with this default configuration or import it in your own
    configuration files before overriding values.
-   use an environment variable to switch between the configurations.
    This can be done from outside the Python interpreter and makes
    development and deployment much easier because you can quickly and
    easily switch between different configs without having to touch the
    code at all.  If you are working often on different projects you can
    even create your own script for sourcing that activates a virtualenv
    and exports the development configuration for you.
-   Use a tool like `fabric`_ in production to push code and
    configurations separately to the production server(s).  For some
    details about how to do that, head over to the
    :ref:`fabric-deployment` pattern.

.. _fabric: http://fabfile.org/


.. _instance-folders:

Instance Folders
----------------

.. versionadded:: 0.8

Flask 0.8 introduces instance folders.  Flask for a long time made it
possible to refer to paths relative to the application's folder directly
(via :attr:`Flask.root_path`).  This was also how many developers loaded
configurations stored next to the application.  Unfortunately however this
only works well if applications are not packages in which case the root
path refers to the contents of the package.

With Flask 0.8 a new attribute was introduced:
:attr:`Flask.instance_path`.  It refers to a new concept called the
“instance folder”.  The instance folder is designed to not be under
version control and be deployment specific.  It's the perfect place to
drop things that either change at runtime or configuration files.

You can either explicitly provide the path of the instance folder when
creating the Flask application or you can let Flask autodetect the
instance folder.  For explicit configuration use the `instance_path`
parameter::

    app = Flask(__name__, instance_path='/path/to/instance/folder')

Please keep in mind that this path *must* be absolute when provided.

If the `instance_path` parameter is not provided the following default
locations are used:

-   Uninstalled module::

        /myapp.py
        /instance

-   Uninstalled package::

        /myapp
            /__init__.py
        /instance

-   Installed module or package::

        $PREFIX/lib/python2.X/site-packages/myapp
        $PREFIX/var/myapp-instance

    ``$PREFIX`` is the prefix of your Python installation.  This can be
    ``/usr`` or the path to your virtualenv.  You can print the value of
    ``sys.prefix`` to see what the prefix is set to.

Since the config object provided loading of configuration files from
relative filenames we made it possible to change the loading via filenames
to be relative to the instance path if wanted.  The behavior of relative
paths in config files can be flipped between “relative to the application
root” (the default) to “relative to instance folder” via the
`instance_relative_config` switch to the application constructor::

    app = Flask(__name__, instance_relative_config=True)

Here is a full example of how to configure Flask to preload the config
from a module and then override the config from a file in the config
folder if it exists::

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object('yourapplication.default_settings')
    app.config.from_pyfile('application.cfg', silent=True)

The path to the instance folder can be found via the
:attr:`Flask.instance_path`.  Flask also provides a shortcut to open a
file from the instance folder with :meth:`Flask.open_instance_resource`.

Example usage for both::

    filename = os.path.join(app.instance_path, 'application.cfg')
    with open(filename) as f:
        config = f.read()

    # or via open_instance_resource:
    with app.open_instance_resource('application.cfg') as f:
        config = f.read()
