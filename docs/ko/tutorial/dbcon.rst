.. _tutorial-dbcon:

스텝 4: 데이터베이스 커넥션 요청하기
------------------------------------

이제 우리는 어떻게 데이터베이스 커넥션을 생성할 수 있고 스크립트에서 어떻게 사용되는지 알고 있다.
하지만 어떻게 하면 좀더 근사하게 커넥션 요청을 할 수 있을까?
우리는 우리의 모든 함수에서 데이터베이스 커넥션을 필요로 한다. 
그러므로 요청이 오기전에 커넥션을 초기화 하고 사용이 끝난 후 종료시키는 것이
합리적이다.

Flask에서는 :meth:`~flask.Flask.before_request` ,
:meth:`~flask.Flask.after_request` 그리고 :meth:`~flask.Flask.teardown_request`
데코레이터(decorators)를 이용할 수 있다.::

    @app.before_request
    def before_request():
        g.db = connect_db()

    @app.teardown_request
    def teardown_request(exception):
        g.db.close()

파라미터가 없는 :meth:`~flask.Flask.before_request` 함수는 리퀘스트가 실행되기 전에 
호출되는 함수이다. :meth:`~flask.Flask.after_request` 함수는 리퀘스트가 실행된 다음에
호출되는 함수이며 클라이언트에게 전송된 응답(reponse)를 파리미터로 넘겨주어야 한다.
이 함수들은 반드시 사용된 응답(response)객체 혹은 새로운 응답(respone)객체를 리턴하여야 한다.
그러나 이 함수들은 예외가 발생할 경우 반드시 실행됨을 보장하지 않는다.
이 경우 예외상황은 :meth:`~flask.Flask.teardown_request` 으로 전달된다. 
이 함수들은 응답객체가 생성된 후 호출된다. 이 ㅎ마수들은 request객체를 수정할 수 없으며,
리턴 값들은 무시된다. 만약 리퀘스트가 진행중에 예외사항이 발생 했을 경우 해당 리퀘스트는
다시 각 함수들에게로 전달되며 그렇지 않을 경우에는 `None` 이 전달된다.


우리는 현재 사용중인 데이터베이스 커넥션을 특별하게 저장한다.
Flask 는 :data:`~flask.g` 라는 특별한 객체를 우리에게 제공한다. 이 객체는 
각 함수들에 대해서 오직 한번의 리퀘스트에 대해서만 유효한 정보를 저장하하고 있다.
쓰레드환경의 경우 다른 객체에서 위와 같이 사용 할경우 작동이 보장되지 않기 때문에
결코 사용해서는 안된다.

이 특별한 :data:`~flask.g` 객체는 보이지않는 뒷편에서 마법과 같은 어떤일을 수행하여 
쓰레드환경에서도 위와같은 사용이 올바르게 작동하도록 해준다.

다음 섹션에서 계속 :ref:`tutorial-views`.

.. hint:: 어느 곳에 이 소스코드를 위치시켜야 하나요?
   
   만얀 당신이 이 튜토리얼을 따라서 여기까지 진행했다면, 아마도 당신은
   이번 스텝과 다음스텝 어디에 코드를 작성해 넣어야 하는지 궁금할 수 있습니다.
   논리적인 위치는 함수들이 함께 그룹핑되는 모듈 레벨의 위치 이고,
   새로 만든 ``before_request`` 와 ``teardown_request`` 함수를 기존의 ``init_db`
   함수 아래에 작성할 수 있다.
   (튜토리얼을 따라 한줄씩 작성한다.)

   만약 현시점에서 각 부분들의 관계를 알고 싶다면, `예제 소스`_ 가 어떻게
   구성되어 있는지 눈여겨 볼 필요가 있다. Flask에서는 하나의 Python 파일에 당신의
   모든 어플리케이션 코드를 다 작성하여 넣는것도 가능하다. 
   물론 정말 그렇게 할 필요는 없다. 만약 당신의 어플리케이션이 :ref:`grows larger <larger-applications>` 
   점점 커져간다면 이것은 좋은 생각이 아니다.

.. _예제 소스:
   http://github.com/mitsuhiko/flask/tree/master/examples/flaskr/
