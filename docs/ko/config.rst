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
                                  개별적으로 후킹하여 :meth:`~flask.Flask.get_send_file_max_age` 를 사용한다.
                                  기본값은 43200초 이다(12 시간).
``TRAP_HTTP_EXCEPTIONS``          만약 이 값이 ``True`` 로 셋팅되어 있다면 Flask는 
                                  HTTP 익셉션 처리를 위한 에러 핸들러를 실행 하지 않는다.
                                  하지만, 대신에 익셉션 스택을 발생시킨다. 이렇게 하면 디버깅이 어려운 상황에서 
                                  HTTP 에러가 발견되는 곳을 찾을 때 유용하다.
``TRAP_BAD_REQUEST_ERRORS``       잘못된 요청(BadRequest)에 대한 주요 익셉션 에러들은 Werkzeug의 내부 데이터 
                                  구조에 의해 다루어 진다. 마찬가지로 많은 작업들이 잘못된 요청에 의해 
                                  암시적으로 일관성부분에서 실패할 수 있다.
                                  이 플래그는 왜 실패가 발생했는지 디버깅 상황에서 명백하게 알고 싶을 때 좋다.
                                  만약 ``True`` 로 설정 되어 있다면, 주기적인 추적값을 얻을 수 있을 것이다.
``PREFERRED_URL_SCHEME``          사용가능한 URL 스키마가 존재하지 않을 경우 해당 URL에 대한 스키마가 
                                  반드시 필요하기 때문에 기본 URL 스키마가 필요하다. 기본값은 ``http``.
``JSON_AS_ASCII``                 Flask 직렬화 객체는 기본으로 아스키로 인코딩된 JSON을 사용한다.
                                  만약 이 값이 ``False`` 로 설정 되어 있다면, Flask는 ASCII로 인코딩하지 않을 것이며
                                  현재의 출력 문자열을 유니코드 문자열로 리턴할 것이다.
                                  ``jsonify`` 는 자동으로 ``utf-8``로 인코딩을 한 후 해당 인스터스로 전송한다.
================================= =========================================

.. 충고:: ``SERVER_NAME`` 에 대해서 조금더
   
   ``SERVER_NAME`` 키는 서브도메인을 지원하기 위해 사용된다.
   Flask는 서브도메인 부분을 실제 서버이름을 모르는 상태에서 추측 할 수
   없기 때문에, 만약 여러분이 Flask가 서브도메인 환경에서 작동하기를 원한다면 
   요구되는 플래그이다. 이것은 또한 세션 쿠키에서도 사용된다.

   서브도메인을 알지 못하는 것은 Flask의 문제 일뿐만 아니라 웹브라우저의
   경우에도 마찬가지이다. 대부분의 최신 웹브라우저들은 점(dot)이 없는 서버이름에 대해서 
   서브도메인간의 쿠키를 허용하지 않는다. 만약 여러분의 서버이름이 ``'localhost'`` 라면 
   여러분은 ``'localhost'`` 에 대해, 그리고 모든 서브도메인에 대해 쿠키를 
   설정 할 수 없을 것이다. 이러한 경우에는 ``'myapplication.local'`` 와 같이 다른 
   서버이름을 선택해야 한다. 그리고 이 이름에 여러분이 사용하기를 원하는 서브도메인을
   호스트 설정이나 로컬의 `bind`_ 설정을 통해서 추가해주어야 한다. 


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

파일을 통하여 설정하기
----------------------

만약 설정을 실제 어플리케이션 패키지의 바깥쪽에 위치한 별도의 파일에 저장할 
수 있다면 좀더 유용할 것이다. 이것은 어플리케이션의 패키징과 배포단계에서 
다양한 패키지 도구 (:ref:`distribute-deployment`) 들을 사용할 수 있도록 해주며,
결과적으로 사후에 설정 파일을 수정 할 수 있도록 해준다.

일반적인 패턴은 다음과 같다::

    app = Flask(__name__)
    app.config.from_object('yourapplication.default_settings')
    app.config.from_envvar('YOURAPPLICATION_SETTINGS')

이 예제 첫부분에서 설정 파일을 `yourapplication.default_settings` 모듈로부터 불러 온 다음
환경설정 값들을 :envvar:`YOURAPPLICATION_SETTINGS` 파일의 내용으로 덮어씌운다. 
이 환경 변수들은 리눅스(Linux) 혹은 OS X 에서는 서버를 시작하기 전에 쉘의 export 명령어로 
설정 할 수도 있다::

    $ export YOURAPPLICATION_SETTINGS=/path/to/settings.cfg
    $ python run-app.py
     * Running on http://127.0.0.1:5000/
     * Restarting with reloader...

윈도우 시스템에서는 내장 명령어인 `set` 을 대신 사용할 수 있다::

    >set YOURAPPLICATION_SETTINGS=\path\to\settings.cfg

설정 파일들은 실제로는 파이썬 파일들이다. 오직 대문자로된 값들만 나중에 실제로 
설정 객체에 저장된다. 그래서 반드시 설정 키값들은 대문자를 사용하여야 한다.

여기 설정 파일에 대한 예제가 있다::

    # Example configuration
    DEBUG = False
    SECRET_KEY = '?\xbf,\xb4\x8d\xa3"<\x9c\xb0@\x0f5\xab,w\xee\x8d$0\x13\x8b83'


아주 초기에 설정을 로드 할수 있도록 확신할 수 있어야 하고, 확장(플러그인)들은 실행시점에 
설정에 접근 할 수 있다. 설정 객체에서 뿐만 아니라 개별 파일에서도 역시 로드할 수 있는 방법이
존재 한다. 완전한 참고를 위해  :class:`~flask.Config` 객체에 대한 문서를 읽으면 된다.


설정 베스트 사례
----------------------------

앞에서 언급한 접근 방법들에 대한 단점은 테스트를 좀더 확실히 해야 한다는 것이다.
이 문제에 대해서 일반적인 100%의 단일 해법은 존재하지 않는다. 하지만, 이러한 경험을 
개선하기 위해 여두해 두어야 할 몇가지가 있다:


1.  여러분의 어플리케이션을 함수에 구현하고 (Flask의) 블루프린트에 등록하자.
    이러한 방법을 통해 어플리케이션에 대해서 다중인스턴스를 생성하여 유닛테스트를
    보다 쉽게 진행 할 수 있다. 필요에 따라 설정값을 전달해주기 위해 이 방법을 사용할 수 있다.
    

2.  임포트 시점에 설정정보를 필요로 하는 코드를 작성하지 않는다.
    만약 여러분이 스스로 설정값에 대해서 오직 요청만 가능하도록 접근을 제한 한다면 
    필요에 의해 나중에 설정 객체를 재설정 할 수 있다.



개발 / 운영(혹은 제품)
------------------------

대부분의 어플리케이션은 하나 이상의 설정(구성)이 필요 하다.
적어도 운영 환경과 개발환경은 독립된 설정값을 가지고 있어야만 한다. 
이것을 다루는 가장 쉬운 방법은 버전 관리를 통하여 항상 로드되는 기본 
설정값을 사용하는 것이다. 그리고 독립된 설정을값들을 필요에 따라 
위에서 언급했던 방식으로 덮어쓰기한다::

    app = Flask(__name__)
    app.config.from_object('yourapplication.default_settings')
    app.config.from_envvar('YOURAPPLICATION_SETTINGS')

그런다음, 여러분은 단지 독립적인 `config.py` 파일을 추가한 후  
``YOURAPPLICATION_SETTINGS=/path/to/config.py`` 를 export 하면 끝난다. 
물론 다른 방법들도 있다. 예를들면, import 혹은 상속과 같은 방법도 가능하다.


장고(Django)의 세계에서는 명시적으로 설정 파일을 ``from yourapplication.default_settings import import *`` 
를 이용해 파일의 상단에 추가 하여 변경 사항은 수작업으로 덮어쓰기 하는 방법이 가장 일반적이다.
또한 ``YOURAPPLICATION_MODE`` 와 환경 변수에 대해서 `production` , `development` 등의 값을 조사하여 
하드코드된 다른 값들을 import 할 수도 있다.

한가지 흥미로운 패턴은 설정에 대해서도 클래스와 상속을 사용할 수 있다는 것이다::


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

이와 같은 설정을 활성화하기 위해서는 단지 
meth:`~flask.Config.from_object`:: 를 호출 하면 된다::

    app.config.from_object('configmodule.ProductionConfig')

여기 많은 다양한 다른 방법이 있지만 이것은 여러분이 설정 파일을 어떻게 관리하기
원하는가에 달려 있다. 여기 몇가지 좋은 권고사항이 있다:


-   버전관리에서 기본 설정을 유지한다.
    각각의 설정 파일을 이전할때에 이 기본 설정 파일을 사용하거나 설정 값을 덮어쓰기 전에 
    기본 설정 파일의 내용을 자신의 파일로 가져오기 
-   설정 사이를 전환할 환경변수를 사용한다.
    이방식은 파이썬 인터프리터 외부에서 수행하고 빠르고 쉽기 때문에 결국 코드를 만지지 않고도 
    다른 설정 사이를 전환 할 수 있기 때문에 개발 및 배포를 훨씬 쉽게 만들어 줄 수 있다.
    만약 여러분이 종종 다른 프로젝트들에서 작업한다면, virtualenv를 구동하는 자신만의 스크립트를 
    생성하여 자신을 위한 개발 설정을 export 하여 사용할 수 있다.
-   코드와 설정을 독립된 운영 서버에 배포하기 위해서  `fabric`_ 과 같은 도구를 사용한다.
    어떻게 할 수 있는지 자세한 내용은 다음의 내용을 참고 하면 된다.
    :ref:`fabric-deployment` 패턴

.. _fabric: http://fabfile.org/


.. _instance-folders:


인스턴스 폴더
----------------

.. versionadded:: 0.8

Flask 0.8 에서 임시 폴더가 도입되었다. 오랫시간동안 Flask는 가능한 
어플리케이션에 대한 상대 경로를 직접 참조 할 수 있도록 해왔다( :attr:`Flask.root_path` 를 통해서).
이것을 통해 어플리케이션의 설정을 바로 옆에 저장하고 불러오는 많은 개발자들이 있었다.
하지만 불행하게도 이 방법은 오직 어플리케이션이 루트 경로가 패키지의 내용을 참고하지 
않는 경우에만 잘 작동 한다. 

Flask 0.8 부터 새로룬 속성이 도입 되었다:
:attr:`Flask.instance_path` . 이 새로운 컨셉의 속성은 “인스턴스 폴더” 라고 불린다.
인스턴스 폴더는 버전 관리와 특정한 배포에 속하지 않도록 설계되었다. 인스턴스 폴더는 
런타임에서의 변경 사항 혹은 설정 파일의 변경 사항에 대한 것들을 보관하기에 완벽한 장소이다.

여러분은 인스턴스 폴더의 경로에 대해 Flask 어플리케이션이 생성될 때 혹은 
Flask가 인스턴스 폴더를 자동으로 탐지 하도록 하여 명백하게 제공 받을 수 있다 
명시적인 설정으로 사용하기 위해서는 `instance_path` 파라미터를 쓸 수 있다::

    app = Flask(__name__, instance_path='/path/to/instance/folder')

이때에 제공되는 폴더의 경로는 절대 경로임을 *반드시* 명심하자.

만약 `instance_path` 파라미터가 인스턴스 폴더를 제공하지 않는 다면
다음의 위치가 기본으로 사용된다:

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

    ``$PREFIX`` 는 파이썬이 설치된 경로의 prefix 이다. 이 것은 
    ``/usr`` 혹은 여러분의 virtualenv 경로이다. 
    ``sys.prefix`` 를 이용해서 현재 설정된 prefix를 출력해 볼 수 있다.

설정 객체가 설정 파일을 상대 경로로 부터 읽어 올 수 있도록 제공 하기 때문에 
우리는 가능한 한 인스턴스 경로에 대한 상대 파일이름을 통해서 로딩을 변경했다.
설정파일이 있는 상대경로의 동작은 “relative to the application root” (디폴트)와 
“relative to instance folder” 사이에서 `instance_relative_config` 어플리케이션 생성자에 의해  
뒤바뀔 수 있다::

    app = Flask(__name__, instance_relative_config=True)

여기 어떻게 Flask에서 모듈의 설정을 미리 로드하고 설정 폴더가 존재 할 경우 설정 파일로 부터 
설정을 덮어쓰기 할 수 있는 전체 예제가 있다 ::

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object('yourapplication.default_settings')
    app.config.from_pyfile('application.cfg', silent=True)

인스턴스 폴더의 경로를 통해 :attr:`Flask.instance_path` 를 찾을 수 있다. 
Flask는 또한 인스턴스 폴더의 파일을 열기 위한 바로가기를 :meth:`Flask.open_instance_resource` 를 통해 제공 한다.


두 경우에 대한 사용 예제::

    filename = os.path.join(app.instance_path, 'application.cfg')
    with open(filename) as f:
        config = f.read()

    # or via open_instance_resource:
    with app.open_instance_resource('application.cfg') as f:
        config = f.read()
