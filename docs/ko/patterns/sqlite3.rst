.. _sqlite3:

Flask에서 SQLite 3 사용하기
==============================

여러분은 Flask에서 필요할 때 데이타베이스 연결을 열고 문맥이 끝났을 때 
(보통 요청이 끝에서) 연결을 닫는 것을 쉽게 구현할 수 있다::

    import sqlite3
    from flask import _app_ctx_stack

    DATABASE = '/path/to/database.db'

    def get_db():
        top = _app_ctx_stack.top
        if not hasattr(top, 'sqlite_db'):
            top.sqlite_db = sqlite3.connect(DATABASE)
        return top.sqlite_db

    @app.teardown_appcontext
    def close_connection(exception):
        top = _app_ctx_stack.top
        if hasattr(top, 'sqlite_db'):
            top.sqlite_db.close()

데이타베이스를 지금 사용하기 위해서 어플리케이션에서 필요한 전부는 활성화된
어플리케이션 문맥을 갖거나 (전달중인 요청이 있다면 항상 활성화 된 것이다)
어플리케이션 문맥 자체를 생성하는 것이다.  그 시점에 ``get_db`` 함수는 현재
데이타베이스 연결을 얻기위해 사용될 수 있다.  그 문맥이 소멸될 때마다
그 데이타베이스 연결은 종료될 것이다.

예제::

    @app.route('/')
    def index():
        cur = get_db().cursor()
        ...


.. note::

   before-request 핸들러가 실패하거나 절대 실행되지 않더라도, teardown 요청과 
   appcontext 함수는 항상 실행되다는 것을 명심하길 바란다. 그런 이유로 우리가 
   데이타베이스를 닫기전에 거기에 데이타베이스가 있었다는 것을 여기서 보장해야한다.

필요할 때 연결하기
------------------

이 접근법의 장점은 (첫 사용시 연결하는 것) 정말 필요할 때만 연결이 열린다는 것이다.
여러분이 요청 문맥 밖에서 이 코드를 사용하고 싶다면 파이썬 쉘에서 수동으로 
어플리케이션 문맥을 열고서 그 연결을 사용할 수 있다::

    with app.app_context():
        # now you can use get_db()

.. _easy-querying:

쉬운 질의하기
-------------

이제 각 요청 핸들링 함수에서 현재 열린 데이타베이스 연결을 얻기 위해 
여러분은 `g.db` 에 접근할 수 있다.  SQLite 로 작업을 간단하게 하기 위해,
행(row) 팩토리 함수가 유용하다.  결과를 변환하기 위해 데이타베이스에서
반환된 모든 결과에 대해 실행된다.  예를 들면 튜플 대신 딕셔너리를 얻기 위해
아래와 같이 사용될 수 있다::

    def make_dicts(cursor, row):
        return dict((cur.description[idx][0], value)
                    for idx, value in enumerate(row))

    db.row_factory = make_dicts

덧붙이자면 커서를 얻고, 결과를 실행하고 꺼내는 것을 결합한 질의 함수를 
제공하는 것은 괜찮은 생각이다::
    
    def query_db(query, args=(), one=False):
        cur = get_db().execute(query, args)
        rv = cur.fetchall()
        cur.close()
        return (rv[0] if rv else None) if one else rv

이 유용한 작은 함수는 행 팩토리와 결합되어 데이타베이스와 작업을 단지 
원형의 커서와 연결 객체를 사용하는 것 보다 훨씬 더 기분 좋게 만든다.

아래에 그것을 사용하는 방법이 있다::

    for user in query_db('select * from users'):
        print user['username'], 'has the id', user['user_id']

또는 여러분이 단지 단일 결과를 원한다면::

    user = query_db('select * from users where username = ?',
                    [the_username], one=True)
    if user is None:
        print 'No such user'
    else:
        print the_username, 'has the id', user['user_id']

변수의 일부분을 SQL 구문으로 전달하기 위해, 구문 안에 물음표를 사용하고
목록으로 인자안에 전달한다.  절대로 직접 인자들을 문자열 형태로 SQL 구문에
추가하면 안되는데 왜냐하면 `SQL 인젝션(Injections)
<http://en.wikipedia.org/wiki/SQL_injection>`_ 을 사용해서 그 어플리케이션을
공격할 수 있기 때문이다.

초기 스키마
-----------

관계형 데이타베이스들은 스키마를 필요로 하기 때문에, 어플리케이션들은 
데이타베이스를 생성하는 `schema.sql` 파일을 종종 만들어낸다.  그 스키마에
기반한 데이타베이스를 생성하는 함수를 제공하는 것은 괜찮은 생각이다.
아래 함수는 여러분을 위해 그러한 작업을 할 수 있다::

    def init_db():
        with app.app_context():
            db = get_db()
            with app.open_resource('schema.sql') as f:
                db.cursor().executescript(f.read())
            db.commit()

그리고 나면 여러분은 파이썬 쉘에서 그런 데이타베이스를 생성할 수 있다:

>>> from yourapplication import init_db
>>> init_db()
