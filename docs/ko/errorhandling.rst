.. _application-errors:

Logging Application Errors
==========================

.. versionadded:: 0.3

어플리케이션이 실패하면 서버도 실패한다. 조만간 여러분은 운영환경에서 예뢰를 보게 될 것이다.
비록 여러분의 코드가 100%가 정확하다 하더라도 여러분은 여전히 가끔씩 예외를 볼 것이다. 왜? 
왜냐하면 포함된 그 밖에 모든 것들이 실패할 것이기 때문이다. 여기에 완벽하게 좋은 코드가 서버 
에러를 발생시킬 수 있는 상황이 있다: 

-   클라이언트가 request를 일찍 없애 버렸는데 여전히 어플리케이션이 입력되는 데이타를 읽고 있는 경우.
-   데이타베이스 서버가 과부하로 인해 쿼리를 다룰 수 없는 경우.
-   파일시스템이 꽉찬 경우
-   하드 드라이브가 크래쉬된 경우
-   백엔드 서버가 과부하 걸린 경우
-   여러분이 사용하고 있는 라이브러에서 프로그래밍 에러가 발생하는 경우
-   서버에서 다른 시스템으로의 네트워크 연결이 실패한 경우

위 상황은 여러분이 직면할 수 있는 이슈들의 작은 예일 뿐이다. 이러한 종류의 문제들을 어떻게 
다루어야 할 까? 기본적으로 어플리케이션이 운영 모드에서 실행되고 있다면, Flask는 매우 
간단한 페이지를 보여주고 :attr:`~flask.Flask.logger` 에 예외를 로깅할 것이다. 

그러나 여러분이 할 수 있는 더 많은 것들이 있다. 우리는 에러를 다루기 위해 더 나은 셋업을 
다룰 것이다. 


메일로 에러 발송하기
-----------

 만약 어플리케이션이 운영 모드에서 실행되고 있다면(여러분의 서버에서) 여러분은 기본으로 
 어떠한 로그 메세지도 보지 못할 것이다. 그건 왜일까? Flask는 설정이 없는 프레임워크가 
 되려고 노력한다. 만약 어떠한 설정도 없다면 Flask는 어디에 로그를 떨어뜨려야 하나? 추측은 
 좋은 아이디어가 아닌다. 왜냐하면 추측되어진 위치는 사용자가 로그 파일을 생성할 권한을 
 가지고 있는 위치가 아니기 때문이다.(?) 또한 어쨌든 대부분의 작은 어플리케이션에서는 아무도 
 로그 파일을 보지 않을 것이다.

사실 어플리케이션 에러에 대한 로그 파일을 설정한다하더라도 사용자가 이슈를 보고 했을 때 
디버깅을 할 때를 제외하고 결코 로그 파일을 보지 않을 것이라는 것을 확신한다. 대신 여러분이 
원하는 것은 예외가 발생했을 때 메일을 받는 것이다. 그리고 나서 여러분은 경보를 받고 그것에 
대한 무언가를 할 수 있다.

Flask는 파이썬에 빌트인된 로깅 시스템을 사용한다. 실제로 에러가 발생했을 때 아마도 
여러분이 원하는 메일을 보낸다. 아래는 예외가 발생했을 때 Flask 로거가 메일을 보내는 것을 
설정하는 방법을 보여준다::

    ADMINS = ['yourname@example.com']
    if not app.debug:
        import logging
        from logging.handlers import SMTPHandler
        mail_handler = SMTPHandler('127.0.0.1',
                                   'server-error@example.com',
                                   ADMINS, 'YourApplication Failed')
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


무슨 일이 일어났는가? 우리는 ``127.0.0.1`` 에서 리스닝하고 있는 메일 서버를 가지고 
“YourApplication Failed”란 제목으로 *server-error@example.com* 송신자로부터 모든 
`관리자` 에게 메일을 보내는 새로운 :class:`~logging.handlers.SMTPHandler` 를 생성했다. 
만약 여러분의 메일 서버가 자격을 
 요구한다면 그것들 또한 제공될 수 있다. 이를 위해 :class:`~logging.handlers.SMTPHandler` 를 위한 문서를 확인해라.

우리는 또한 단지 에러와 더 심각한 메세지를 보내라고 핸들러에게 말한다. 왜냐하면 우리는 주의 
사항이나 요청을 핸들링하는 동안 발생할 수 있는 쓸데없는 로그들을에 대한 메일을 받는 것을 
원하지 않는다

여러분이 운영 환경에서 이것을 실행하기 전에, 에러 메일 안에 더 많은 정보를 넣기 위해  :ref:`logformat`  챕터를 보아라. 그것은 많은 불만으로부터 너를 구해줄 것이다. 



파일에 로깅하기
-----------------

여러분이 메일을 받는다 하더라도, 여러분은 아마 주의사항을 로깅하기를 원할지도 모른다. 
문제를 디버그하기 위해 요구되어질 수 있는 많은 정보를 많이 유지하는 것은 좋은 생각이다. 
Flask는 자체적으로 코어 시스템에서 어떠한 주의사항도 발생하지 않는다는 것을 주목해라. 
그러므로 무언가 이상해 보일 때 코드 안에 주의사항을 남기는 것은 여러분의 책임이다. 

로깅 시스템에 의해 제공되는 몇가지 핸들러가 있다. 그러나 기본 에러 로깅을 위해 그것들 모두가 
유용한 것은 아니다. 가장 흥미로운 것은 아마 아래오 같은 것들일 것이다:

-   :class:`~logging.FileHandler` - 파일 시스템 내 파일에 메세지를 남긴다.
-   :class:`~logging.handlers.RotatingFileHandler` - 파일 시스템 내 파일에 메세지를 남기며 특정 횟수로 순환한다.
-   :class:`~logging.handlers.NTEventLogHandler` - 윈도 시스템의 시스템 이벤트 로그에 로깅할 것이다. 만약 여러분이 윈도에 디플로이를 한다면 이 방법이 사용하기 원하는 방법일 것이다.
-   :class:`~logging.handlers.SysLogHandler` -     유닉스 syslog에 로그를 보낸다.


일단 여러분이 로그 핸들러를 선택하면, 위에서 설명한 SMTP 핸들러를 가지고 여러분이 했던 더 낮은 레벨을 설정하는 것만 확인하라(필자는 WARNING을 추천한다.)::


    if not app.debug:
        import logging
        from themodule import TheHandlerYouWant
        file_handler = TheHandlerYouWant(...)
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)

.. _logformat:

로그 포맷 다루기
--------------------------

기본으로 해들러는 단지 파일 안에 메세지 문자열을 쓰거나 메일로 여러분에 메세지를 보내기만 할 것이다. 로그 기록은 더 많은 정보를 저장한다. 왜 에러가 발생했는니나 더 중요한 어디서 에러가 발생했는지 등의 더 많은 정보를 포함하도록 로거를 설정할 수 있다.

포매터는 포맷 문자열을 가지고 초기화될 수 있다. 자동으로 역추적이 로그 진입점에 추가되어진다는 것을 주목하라.(?) 여러분은 로그 포맷터 포맷 문자열안에 그걸 할 필요가 없다.

여기 몇가지 셋업 샘플들이 있다:

이메일
`````

::

    from logging import Formatter
    mail_handler.setFormatter(Formatter('''
    Message type:       %(levelname)s
    Location:           %(pathname)s:%(lineno)d
    Module:             %(module)s
    Function:           %(funcName)s
    Time:               %(asctime)s

    Message:

    %(message)s
    '''))

파일 로깅
````````````

::

    from logging import Formatter
    file_handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))


복잡한 로그 포맷
``````````````````````

여기에 포맷 문자열을 위한 유용한 포맷팅 변수 목록이 있다. 이 목록은 완전하지는 않으며 전체 리스트를 보려면 :mod:`logging`  의 공식 문서를 참조하라.


.. tabularcolumns:: |p{3cm}|p{12cm}|

+------------------+----------------------------------------------------+
| Format           | Description                                        |
+==================+====================================================+
| ``%(levelname)s``| 메시지를 위한 텍스트 로깅 레벨                 |
|                  | (``'DEBUG'``, ``'INFO'``, ``'WARNING'``,           |
|                  | ``'ERROR'``, ``'CRITICAL'``).                      |
+------------------+----------------------------------------------------+
| ``%(pathname)s`` | 로깅이 호출되는 소스 파일의 전체 경로(사용 가능하다면).            |
+------------------+----------------------------------------------------+
| ``%(filename)s`` | 전체 경로 중 파일명.                      |
+------------------+----------------------------------------------------+
| ``%(module)s``   | 모듈(파일명 중 이름 부분).                 |
+------------------+----------------------------------------------------+
| ``%(funcName)s`` | 로깅 호출을 포함하는 함수명.      |
+------------------+----------------------------------------------------+
| ``%(lineno)d``   | 로깅이 호출되는 소스 라인 번호(사용 가능하다면)|
+------------------+----------------------------------------------------+
| ``%(asctime)s``  | 사람이 읽을 수 있는 형태의 시간 메시지        |
|                  |   다음은 기본 포맷이다.           |
|                  | ``"2003-07-08 16:49:45,896"`` (콤마 다음 숫자는 밀리세컨드이다)   |
|                  | 이것은 formatter를 상속받고   |
|                  |  :meth:`~logging.Formatter.formatTime` 메소드를 오버라이드하여 변경할 수 있다                                 |
+------------------+----------------------------------------------------+
| ``%(message)s``  | ``msg % args`` 에 의해 계산된 로그 메시지     |
+------------------+----------------------------------------------------+

만약 여러분이 포맷티을 더 커스터마이징하기를 원한다면 포맷터를 상속받을 수 있다. 그 포매터는 세가지 흥미로운 메소드를 가지고 있다: 

:meth:`~logging.Formatter.format`:
    실제 포매팅을 다룬다. :class:`~logging.LogRecord` 객체를 전달하면 포매팅된 문자열을 반환해야 한다.
:meth:`~logging.Formatter.formatTime`:
    called for `asctime` 포매팅을 위해 호출된다. 만약 다른 시간 포맷을 원한다면 이 메소드를 오버라이드할 수 있다.
:meth:`~logging.Formatter.formatException`
    예외 포매팅을 위해 호출된다. :attr:`~sys.exc_info` 튜플을 전달하면 문자열을 반환해야 한다. 보통 기본으로 사용해도 괜찮으며, 굳이 오버라이드할 필요는 없다.

더 많은 정보를 위해서 공식 문서를 참조해라. 


다른 라이브러리들
---------------

이제까지는 우리는 단지 여러분의 어플리케이션이 생성한 로거를 설정했다. 다른 라이브러리들 
또한 로그를 남길 수 있다. 예를 들면 SQLAlchemy가 그것의 코어 안에서 무겁게 로깅을 사용한다.
:mod:`logging` 패키지 안에 모든 로거들을 설정할 방법이 있지만 나는 그거을 사용하는 것을 
추천하지 않는다. 여러분이 같은 파이썬 인터프리터에서 같이 실행되는 여러 개로 분리된 
어플리케이션을 갖기를 원할 수도 있다. 이러한 상황을 위해 다른 로깅을 셋업하는 것은 
불가능하다. 

대신 :func:`~logging.getLogger` 함수를 가지고 로거들을 얻고 핸들러를 첨부하기 위해 얻은 
로거들을 반복하여 여러분이 관심있어 하는 로거들을 만드는 것을 추천한다::


    from logging import getLogger
    loggers = [app.logger, getLogger('sqlalchemy'),
               getLogger('otherlibrary')]
    for logger in loggers:
        logger.addHandler(mail_handler)
        logger.addHandler(file_handler)


어플리케이션 에러 디버깅
============================

제품화된 어플리케이션의 경우, :ref:`application-errors` 에 설명된것을 참고하여
로깅과 알림설정을 구성하는 것이 좋다. 이 섹션은 디버깅을 위한 설정으로 배포할때 
완전한 기능을 갖춘 Python 디버거를 깊이있게 사용하는 방법을 제공한다. 



의심이 들때는 수동으로 실행하자
---------------------------

제품화를 위해 설정된 어플리케이션에서 문제를 겪고 있는가?
만약 해당 호스트에 쉘 접근 권한을 가지고 있다면, 배포 환경에서 쉘을 이용해
수동으로 어플리케이션을 실행 할 수 있는지 확인한다.
권한에 관련된 문제를 해결하기 위해서는 배포환경에 설정된 것과 동일한 사용자
계정에서 실행되어야 한다. 제품화된 운영 호스트에서 `debug=True` 를 이용하여 
Flask에 내장된 개발 서버를 사용하면 설정 문제를 해결하는데 도움이되지만, 
**이와같은 설정은 통제된 환경에서 임시적으로만 사용해야 함을 명심하자.**
`debug=True` 설정은 운영환경 혹은 제품화되었을때는 절대 사용해서는 안된다.


.. _working-with-debuggers:


디버거로 작업하기
----------------------

좀더깊이 들어가서 코드 실행을 추적한다면, Flask는 독자적인 디버거를 제공한다.
(:ref:`debug-mode` 참고) 만약 또다른 Python 디버거를 사용하고 싶다면 이 디버거들은
서로 간섭현상이 발생하므로 주의가 필요하다. 선호하는 디버거를 사용하기 위해서는 
몇몇  디버깅 옵션을 설정해야만 한다.:

* ``debug``        - 디버그 모드를 사용하고 예외를 잡을 수 있는지 여부
* ``use_debugger`` - Flask 내부 디버거를 사용할지 여부
* ``use_reloader`` - 예외발생시 프로세스를 포크하고 리로드할지 여부

``debug`` 옵션은 다른 두 옵션 이 어떤값을 갖던지 반드시 True 이어야 한다. 
(즉, 예외는 잡아야만 한다.) 

만약 Eclipse에서 Aptana를 디버깅을 위해 사용하고 싶다면, ``use_debugger` 와 `use_reloader``
옵션을 False로 설정해야 한다.

config.yaml을 이용해서 다음과 같은 유용한 설정패턴을 사용하는 것이 가능하다
(물론 자신의 어플리케이션을위해 적절하게 블럭안의 값들을 변경시킬 수 있다.)::

   FLASK:
       DEBUG: True
       DEBUG_WITH_APTANA: True

이렇게 설정한다음 어플리케이션의 시작점(main.py)에 다음과 같이 사용할 수 있다.::

   if __name__ == "__main__":
       # To allow aptana to receive errors, set use_debugger=False
       app = create_app(config="config.yaml")

       if app.debug: use_debugger = True
       try:
           # Disable Flask's debugger if external debugger is requested
           use_debugger = not(app.config.get('DEBUG_WITH_APTANA'))
       except:
           pass
       app.run(use_debugger=use_debugger, debug=app.debug,
               use_reloader=use_debugger, host='0.0.0.0')
