.. _sqlite3:

플라스크에서 SQLite 3 사용하기
==============================

여러분은 플라스크에서 필요할 때 데이타베이스 연결을 열고 문맥이 끝났을 때 
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

This handy little function in combination with a row factory makes working
with the database much more pleasant than it is by just using the raw
cursor and connection objects.

Here is how you can use it::

    for user in query_db('select * from users'):
        print user['username'], 'has the id', user['user_id']

Or if you just want a single result::

    user = query_db('select * from users where username = ?',
                    [the_username], one=True)
    if user is None:
        print 'No such user'
    else:
        print the_username, 'has the id', user['user_id']

To pass variable parts to the SQL statement, use a question mark in the
statement and pass in the arguments as a list.  Never directly add them to
the SQL statement with string formatting because this makes it possible
to attack the application using `SQL Injections
<http://en.wikipedia.org/wiki/SQL_injection>`_.

Initial Schemas
---------------

Relational databases need schemas, so applications often ship a
`schema.sql` file that creates the database.  It's a good idea to provide
a function that creates the database based on that schema.  This function
can do that for you::

    def init_db():
        with app.app_context():
            db = get_db()
            with app.open_resource('schema.sql') as f:
                db.cursor().executescript(f.read())
            db.commit()

You can then create such a database from the python shell:

>>> from yourapplication import init_db
>>> init_db()
