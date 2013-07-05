.. _tutorial-setup:

스텝 2: 어플리케이션 셋업 코드
==============================

이제 우리는 데이터베이스 스키마를 가지고 있고 어플리케이션 모듈을 생성할 수 있다.
우리가 만들 어플리케이션을 `flaskr` 폴더안에 있는 `flaskr.py` 라고 부르자.
시작하는 사람들을 위하여 우리는 import가 필요한 모듈 뿐만 아니라 설정 영역도 추가할 것이다. 
소규모 어플리케이션을 위해서는 우리가 여기에서 할 모듈 안에 설정을 직접 추가하는 것이 가능하다. 
그러나 더 깔끔한 해결책은 설정을 `.ini` 또는 `.py` 로 분리하여 생성하여 로드하거나 그 파일로부터 
값들을 import하는 것이다.  


아래는 flaskr.py 파일 내용이다: 


In `flaskr.py`::

    # all the imports
    import sqlite3
    from flask import Flask, request, session, g, redirect, url_for, \
         abort, render_template, flash

    # configuration
    DATABASE = '/tmp/flaskr.db'
    DEBUG = True
    SECRET_KEY = 'development key'
    USERNAME = 'admin'
    PASSWORD = 'default'


다음으로 우리는 우리의 실제 어플리케이션을 생성하고 같은 파일의 설정을 가지고
어플리케이션을 초기화할 수 있다. `flaskr.py` 내용은 ::


    # create our little application :)
    app = Flask(__name__)
    app.config.from_object(__name__)

:meth:`~flask.Config.from_object` 는 인자로 주어진 객체를 설정값을 읽어 오기 위해 살펴 볼 것이다.
(만약 인자 값이 문자열이면 해당 객체를 임포트 할것이다.) 그리고나서 거기에 정의된 모든 대문자 
변수들을 찾을 것이다. 우리의 경우, 우리가 위에서 몇 줄의 코드로 작성했던 설정이다. 
여러분은 분리된 파일로도 설정값들을 이동시킬 수 있다. 

일반적으로 설정 파일에서 설정값을 로드하는 것은 좋은 생각이다. 
위에서 사용한 :meth:`~flask.Config.from_object` 대신 :meth:`~flask.Config.from_envvar` 
를 사용하여 설정값을 로드할 수도 있다:: 

    app.config.from_envvar('FLASKR_SETTINGS', silent=True)

위와 같은 방식으로 환경변수를 호출하여 설정값을 로드할 수도 있다.
:envvar:`FLASKR_SETTINGS` 에 명시된 설정 파일이 로드되면 기본 설정값들은 덮어쓰기가 된다.
silent 스위치는 해당 환경변수가 존재 하지 않아도 Flask가 작동하도록 하는 것이다.

클라이언트에서의 세션을 안전하게 보장하기 위해서는 `secret_key` 가 필요하다.
secret_key는 추측이 어렵도록 가능한 복잡하게 선택하여야 한다.
디버그 플래그는 인터랙ㅌ브 디버거를 활성화 시키거나 비활성화 시키는 일을 한다.
*운영시스템에서는 디버그 모드를 절대로 활성화 시키지 말아야 한다.*
왜냐하면 디버그 모드에서는 사용자가 서버의 코드를 실행할수가 있기 때문이다.


우리는 또한 명세화된 데이터베이스에 쉽게 접속할 수 있는 방법을 추가할 것이다.
이방법으로 Python 인터랙티브 쉘이나 스크립트에서 요청에 의해 커넥션을 
얻기위해 사용할 수 있다. 이 방법을 뒤에서 좀더 편리하게 만들어 볼 것이다.


::

    def connect_db():
        return sqlite3.connect(app.config['DATABASE'])

마지막으로 우리는 파일의 마지막에 단독 서버로 실행되는 애플리케이션을 위한  
서버 실행 코드를 한줄 추가 하였다.::

    if __name__ == '__main__':
        app.run()

여기까지 되어있으면 문제없이 어플리케이션을 시작할 수 있어야 한다.
다음 명령어로 실행이 가능하다::

   python flaskr.py

서버가 접근가능한 주소로 실행되었다고 알려주는 메시지를 
접할 수 있을 것이다.

우리가 아직 아무런 뷰(view)를 만들지 않았기 때문에 브라우저에서는 페이지를
찾을 수 없다는 404에러를 볼 수 있을 것이다. 이부분에 대해서는 좀 더 후에
살펴 보도록 할 것이다. 먼저 살펴봐야 할 것은 데이터베이스가 작동되는지 확인하는 것이다.


.. admonition:: 외부에서 접근가능한 서버 

   당신의 서버를 외부에 공개하고 싶다면 다음 섹션을 참고 하라
   :ref:`externally visible server <public-server>` 

Continue with :ref:`tutorial-dbinit`.
