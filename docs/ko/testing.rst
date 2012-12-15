.. _testing:

플라스크 어플리케이션 테스트하기
==========================

   **Something that is untested is broken.**

이 문구의 기원을 정확하게 알수는 없지만, 이것은 진실에 가깝다.
테스트되지 않은 어플리케이션은들은 기존 코드의 개선을 어렵게 하며 프로그램
개발자들을 심한 편집증환자로 만들어 버린다. 만약 어플리케이션의 테스트들이
자동화 되어 있다면, 우리는 문제가 발생했을때 안전하며 즉각적으로 변경이 가능하다.

Flask는 Werkzeug 를 통해 테스트 :class:`~werkzeug.test.Client` 를 제공하여
어플리케이션의 컨텍스트 로컬을 처리하고 테스트할 수 있는 방법을 제공한다. 
그리고 당신이 가장 좋아하는 테스팅 도구를 사용 할 수 있도록 해준다.
이 문서에서 우리는 Python에서 기본으로 제공하는 :mod:`unittest`  를
사용 할 것이다.


어플리케이션
---------------

첫째로 우리는 테스트할 어플리케이션이 필요하다. 우리는 :ref:`tutorial` 에서 
소개된 어플리케이션을 사용할 것이다. 아직 어플리케이션이 준비되지 않았다면 
`the examples`_ 에서 소스코드를 준비하자.

.. _the examples:
   http://github.com/mitsuhiko/flask/tree/master/examples/flaskr/


테스팅 스켈레톤(Skeleton)
--------------------

어플리케이션을 테스트 하기 위해서, 우리는 두번째 모듈 (`flaskr_tests.py`) 을
추가하고 단위테스트 스켈레톤(Skeleton)을 만든다.::

    import os
    import flaskr
    import unittest
    import tempfile

    class FlaskrTestCase(unittest.TestCase):

        def setUp(self):
            self.db_fd, flaskr.app.config['DATABASE'] = tempfile.mkstemp()
            flaskr.app.config['TESTING'] = True
            self.app = flaskr.app.test_client()
            flaskr.init_db()

        def tearDown(self):
            os.close(self.db_fd)
            os.unlink(flaskr.app.config['DATABASE'])

    if __name__ == '__main__':
        unittest.main()

:meth:`~unittest.TestCase.setUp` 함수의 코드는 새로운 테스트 클라이어트를
생성하고 새로운 데이터베이스를 초기화 한다. 이 함수는 각각의 테스트 함수가
실행되기 전에 먼저 호출된다. 테스트후 데이터베이스를 삭제하기 위해 
:meth:`~unittest.TestCase.tearDown` 함수에서 파일을 닫고 파일시스템에서 
제거 할 수 있다. 또한 setup 함수가 실행되는 동안에 ``TESTING`` 플래그(flag)가
활성화된다. 요청을 처리하는 동안에 오류 잡기(error catch)가 비활성화되어
있는 것은 어플리케이션에대한 성능테스트에 대하여 좀 더 나은 오류 리포트를 얻기
위해서이다.

이 테스트 클라이언트는 어플리케이션에대한 단순한 인터페이스를 제공한다.
우리는 어플리케이션에게 테스트 요청을 실행시킬 수 있고, 테스트 클라이언트는
이를 위해 쿠키를 놓치지 않고 기록한다.

SQLite3는 파일시스템 기반이기 때문에 임시 데이터베이스를 생성할때 tempfile 모듈을 
사용하여 초기화 할 수 있다. :func:`~tempfile.mkstemp`  함수는 두가지 작업을 수행한다:
이 함수는 로우-레벨 파일핸들과 임의의 파일이름을 리턴한다. 여기서 임의의 파일이름을
데이터베이스 이름으로 사용한다. 우리는 단지 `db_fd` 라는 파일핸들을 :func:`os.close` 함수를 
사용하여 파일을 닫기전까지 유지하면 된다. 

만약 지금 테스트 실행한다면, 다음과 같은 출력내용을 볼 수 있을 것이다.::

    $ python flaskr_tests.py

    ----------------------------------------------------------------------
    Ran 0 tests in 0.000s

    OK

비록 실제 테스트를 실행하지는 않았지만, 우리는 이미 flaskr 어플리케이션의
문법구문상으로 유효하다는 것을 벌써 알게되었다, 그렇지 않다면 어플리케이션이
종료되는 예외상황을 겪었을 것이다.


첫번째 테스트
--------------

이제 어플리케이션의의 기능 테스트를 시작할 시간이다.
어플리케이션의 루트 (``/``)로 접근하였을때 어플리케이션이 
"No entries here so far" 를 보여주는지 확인해야 한다.
이 작업을 수행하기 위해서, 우리는 새로운 테스트 메소드를
다음과 같이 클래스에 추가하여야 한다.::

    class FlaskrTestCase(unittest.TestCase):

        def setUp(self):
            self.db_fd, flaskr.app.config['DATABASE'] = tempfile.mkstemp()
            self.app = flaskr.app.test_client()
            flaskr.init_db()

        def tearDown(self):
            os.close(self.db_fd)
            os.unlink(flaskr.DATABASE)

        def test_empty_db(self):
            rv = self.app.get('/')
            assert 'No entries here so far' in rv.data

우리의 테스트 함수들의 이름이 `test` 로 시작하고 있다는 것에 주목하자.
이점을 활용하여 :mod:`unittest` 에서 테스트를 수행할 함수를 자동적으로 식별할 수 있다.

`self.app.get` 를 사용함으로써 HTTP `GET` 요청을 주어진 경로에 보낼 수 있다.
리턴값은 :class:`~flask.Flask.response_class` 객체의 값이 될 것이다.
이제 :attr:`~werkzeug.wrappers.BaseResponse.data` 의 속성을 사용하여 어플리케이션
으로부터 넘어온 리턴 값(문자열)을 검사 할 수 있다.
이런 경우, ``'No entries here so far'`` 가 출력 메시지에 포함되어 있는 것을 확인해야 한다.

다시 실행해 보면 하나의 테스트에 통과 한 것을 확인할 수 있을 수 있을 것이다. ::

    $ python flaskr_tests.py
    .
    ----------------------------------------------------------------------
    Ran 1 test in 0.034s

    OK


입력과 출력 로깅
------------------

우리의 어플리케이션에서 대부분의 기능은 관리자만 사용이 가능하다.
그래서 우리의 테스트 클라이언트에서는 어플리케이션의 입력과 출력에대한 
로그를 기록할 수 있어야 한다. 이 작업을 작동시키려면, 로그인과 로그아웃 
페이지요청들에 폼 데이터(사용자이름과 암호) 를 적용해야 한다.
그리고 로그인과 로그아웃 페이지들은 리다이렉트(Redirect)되기 때문에
클라이언트에게 `follow_redirects` 를 설정해 주어야 한다.

다음의 두 함수를 `FlaskrTestCase` 클래스에 추가 하자 ::

   def login(self, username, password):
       return self.app.post('/login', data=dict(
           username=username,
           password=password
       ), follow_redirects=True)

   def logout(self):
       return self.app.get('/logout', follow_redirects=True)


이제 로그인과 로그아웃에 대해서 잘 작동하는지, 유효하지 않은 자격증명에 대해서 실패 하는지
쉽게 테스트 하고 로깅 할 수 있다. 다음의 새로운 테스트를 클래스에 추가 하자::

   def test_login_logout(self):
       rv = self.login('admin', 'default')
       assert 'You were logged in' in rv.data
       rv = self.logout()
       assert 'You were logged out' in rv.data
       rv = self.login('adminx', 'default')
       assert 'Invalid username' in rv.data
       rv = self.login('admin', 'defaultx')
       assert 'Invalid password' in rv.data


메시지 추가 테스트
--------------------

메시지를 추가 하게 되면 잘 작동하는지 확인해야만 한다.
새로운 테스트 함수를 다음과 같이 추가 하자 ::

    def test_messages(self):
        self.login('admin', 'default')
        rv = self.app.post('/add', data=dict(
            title='<Hello>',
            text='<strong>HTML</strong> allowed here'
        ), follow_redirects=True)
        assert 'No entries here so far' not in rv.data
        assert '&lt;Hello&gt;' in rv.data
        assert '<strong>HTML</strong> allowed here' in rv.data

여기에서 우리가 의도한 대로 제목을 제외한 부분에서 HTML이 사용가능한지 확인한다.

이제 실행 하면 세가지 테스트를 통과 할 것이다.::

    $ python flaskr_tests.py
    ...
    ----------------------------------------------------------------------
    Ran 3 tests in 0.332s

    OK

헤더값들과 상태코드들이 포함된 보다 복잡한 테스트를 위해서는,
`MiniTwit Example`_ 예제 소스의 좀 더 큰 어플리케이션의 테스트 수헹방법을 확인하자.


.. _MiniTwit Example:
   http://github.com/mitsuhiko/flask/tree/master/examples/minitwit/


다른 테스팅 기법들
--------------------

위에서 살펴본 대로 테스트 클라이언트를 사용하는 것 이외에,
:meth:`~flask.Flask.test_request_context`  함수를 `with` 구문과 조합하여
요청 컨텍스트를 임시적으로 할성화 하기 위해 사용 될 수 있다. 
이것을 이용하여 :class:`~flask.request` , :class:`~flask.g` 과  :class:`~flask.session` 
같은 뷰 함수들에서 사용하는 객체들에 접근 할 수 있다. 
다음 예제는 이런 방법들을 보여주는 전체 예제이다.::


    app = flask.Flask(__name__)

    with app.test_request_context('/?name=Peter'):
        assert flask.request.path == '/'
        assert flask.request.args['name'] == 'Peter'

컨텍스트와 함께 바인드된 모든 객체는 같은 방법으로 사용이 가능하다.

만약 서로 다른 설정구성으로 어플리케이션을 테스트하기 원할경우 이것을
해결하기 위한 좋은 방법은 없는것 같다. 이와 같이 어플리케이션을 테스트
하려면 어플리케이션 팩토리에 대해서 고혀해 보길 바란다. (참고 :ref:`app-factories`)

그러나 만약 테스트 요청 컨텍스트를 사용하는 경우 :meth:`~flask.Flask.before_request`  
함수 와 :meth:`~flask.Flask.after_request` 는 자동으로 호출되지 않는다.
반면에:meth:`~flask.Flask.teardown_request` 함수는 `with` 블럭에서 요청 컨텍스트를 
빠져나올때 실제로 실행된다. 
만약 :meth:`~flask.Flask.before_request` 함수도 마찬가지로 호출되기를 원한다면,
:meth:`~flask.Flask.preprocess_request` 를 직접 호출해야 한다.::

    app = flask.Flask(__name__)

    with app.test_request_context('/?name=Peter'):
        app.preprocess_request()
        ...

이경우 어플리케이션이 어떻게 설계되었느냐에 따라 데이터베이스 컨넥션 연결이 
필요할 수도 있다.

만약 :meth:`~flask.Flask.after_request` 함수를 호출하려 한다면, :meth:`~flask.Flask.process_response`
함수에 응답객체(Response Object)를 전달하여 직접 호출하여야 한다::

    app = flask.Flask(__name__)

    with app.test_request_context('/?name=Peter'):
        resp = Response('...')
        resp = app.process_response(resp)
        ...

이같은 방식은 일반적으로 해당 시점에 직접 테스트 클라이언트를 사용 할 수
있기 때문에 크게 유용한 방법은 아니다.


컨텍스트 유지시키기
--------------------------

.. versionadded:: 0.4

때로는 일반적인 요청이 실행되는 경우에도 테스트 검증이 필요해질 경우가 
있기 때문에 컨텍스트 정보를 좀더 유지 하는 것이 도움이 될 수 있다.
Flask 0.4 버전에서 부터는 :meth:`~flask.Flask.test_client` 를 `with` 블럭과 함께
사용하면 가능하다.:: 

    app = flask.Flask(__name__)

    with app.test_client() as c:
        rv = c.get('/?tequila=42')
        assert request.args['tequila'] == '42'

만약 :meth:`~flask.Flask.test_client` 를 `with` 블럭이 없이 사용한다면 , 
`request` 가 더이상 유효하지 않기 때문에 `assert` 가 실패 하게 된다.
(그 이유는 실제 요청의 바깥에서 사용하려고 했기 때문이다.)


세션에 접근하고 수정하기
--------------------------------

.. versionadded:: 0.8

때로는 테스트 클라이언트에서  세션에 접근하고 수정하는 일은 매우 유용할 수 있다.
일반적으로 이를 위한 두가지 방법이 있다. 만약 세션이 특정 키 값으로 설정이 되어 있고
그 값이 컨텍스트를 통해서 유지 된다고 접근 가능한것을 보장하는 경우 :data:`flask.session`::

    with app.test_client() as c:
        rv = c.get('/')
        assert flask.session['foo'] == 42


그렇지만 이와 같은 경우는 세션을 수정하거나 접급하는 하는 것을 요청이 실행되기전에
가능하도록 해주지는 않는다. Flask 0.8 버전 부터는 "세션 트랜잭션(session transparent)"
이라고 부르는 세션에 대한 적절한 호출과 테스트 클라이언트에서의 수정이 가능한지
시뮬레이션이 가능하도록 하고 있다. 트랜잭션의 끝에서 해당 세션은 저장된다.
이것은 백엔드(backend)에서 사용되었던 세션과 독립적으로 작동가능하다.::

    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess['a_key'] = 'a value'

        # once this is reached the session was stored

이경우에 :data:`flask.session` 프록시의 ``sess`` 객체를  대신에 사용하여야 함을 
주의하자. 이 객체는 동일한 인터페이스를 제공한다. 
