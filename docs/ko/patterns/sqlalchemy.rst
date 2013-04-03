.. _sqlalchemy-pattern:

플라스크에서 SQLAlchemy 사용하기
================================

많은 사람들이 데이타베이스에 접근하기 위해 `SQLAlchemy`_ 선호한다.
이런 경우 여러분의 플라스크 어플리케이션에 대해 모듈 보다는 패키지를 
사용하고 모델들을 분리된 모듈로 만드는 것이 독려된다(:ref:`larger-applications`).
그것이 필수는 아니지만, 많은 부분에서 이해가 될만하다.

There are four very common ways to use SQLAlchemy를 사용하는 매우 일반적인
네가지 방식이 있다.  여기서 그것들을 각각 간략하게 설명할 것이다:

플라스크-SQLAlchemy 확장
------------------------

SQLAlchemy는 공통 데이타베이스 추상 계층이고 설정하는데 약간의 노력을 요하는
객체 관계형 맵퍼(mapper)이기 때문에, 여러분을 위해 그 역할을 해줄 플라스크 
확장(extension)이 있다.  여러분이 빨리 시작하기를 원한다면 이 방식을 추천한다.

여러분은 `PyPI<http://pypi.python.org/pypi/Flask-SQLAlchemy>`_ 에서 
`플라스크-SQLAlchemy`_ 를 받을 수 있다. 

.. _Flask-SQLAlchemy: http://packages.python.org/Flask-SQLAlchemy/


선언부(Declarative)
-------------------

SQLAlchemy에서 선언부(declarative) 확장은 SQLAlchemy를 사용하는 가장 최신
방법이다.  그 방법은 여러분이 한꺼번에 테이블들과 모델들을 정의하도록 해주는데,
그 방식은 Django(장고)가 동작하는 방식과 유사하다.  다음의 내용에 추가하여 
`declarative`_ 확장에 대한 공식 문서를 권고한다.

아래는 여러분의 어플리케이션을 위해 `database.py` 모듈의 예제이다::

    from sqlalchemy import create_engine
    from sqlalchemy.orm import scoped_session, sessionmaker
    from sqlalchemy.ext.declarative import declarative_base

    engine = create_engine('sqlite:////tmp/test.db', convert_unicode=True)
    db_session = scoped_session(sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=engine))
    Base = declarative_base()
    Base.query = db_session.query_property()

    def init_db():
        # import all modules here that might define models so that
        # they will be registered properly on the metadata.  Otherwise
        # you will have to import them first before calling init_db()
        import yourapplication.models
        Base.metadata.create_all(bind=engine)

모델들을 정의하기 위해, 위의 코드로 생성된 `Base` 클래스를 상속하면 된다.
여러분이 왜 우리가 여기서 쓰레드를 신경쓰지 않아도 되는지 궁금하다면
(위의 SQLite3 예제에서 :data:`~flask.g` 객체를 가지고 한 것 처럼): 
that's because SQLAlchemy does that for us already with the :class:`~sqlalchemy.orm.scoped_session`.
그것은 SQLAlchemy가 :class:`~sqlalchemy.orm.scoped_session` 을 가지고
여러분을 위해서 이미 그러한 작업을 했기 때문이다.

여러분의 어플리케이션에서 선언적인 방식으로 SQLAlchemy를 사용하려면,
여러분의 어플리케이션 모듈에 아래의 코드를 집어넣기만 하면 된다.
플라스크는 여러분을 위해 요청의 끝에서 데이타베이스 세션을 제거할 것이다::

    from yourapplication.database import db_session

    @app.teardown_request
    def shutdown_session(exception=None):
        db_session.remove()

아래는 예제 모델이다  (이 코드를 `models.py` 에 넣어라, e.g.)::

    from sqlalchemy import Column, Integer, String
    from yourapplication.database import Base

    class User(Base):
        __tablename__ = 'users'
        id = Column(Integer, primary_key=True)
        name = Column(String(50), unique=True)
        email = Column(String(120), unique=True)

        def __init__(self, name=None, email=None):
            self.name = name
            self.email = email

        def __repr__(self):
            return '<User %r>' % (self.name)

데이타베이스를 생성하기 위해서 여러분은 `init_db` 함수를 사용할 수 있다:

>>> from yourapplication.database import init_db
>>> init_db()

여러분은 아래와 같이 항목들을 데이타베이스에 추가할 수 있다:

>>> from yourapplication.database import db_session
>>> from yourapplication.models import User
>>> u = User('admin', 'admin@localhost')
>>> db_session.add(u)
>>> db_session.commit()

질의하는것 또한 간단하다::

>>> User.query.all()
[<User u'admin'>]
>>> User.query.filter(User.name == 'admin').first()
<User u'admin'>

.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _declarative:
   http://www.sqlalchemy.org/docs/orm/extensions/declarative.html

Manual Object Relational Mapping
--------------------------------

Manual object relational mapping has a few upsides and a few downsides
versus the declarative approach from above.  The main difference is that
you define tables and classes separately and map them together.  It's more
flexible but a little more to type.  In general it works like the
declarative approach, so make sure to also split up your application into
multiple modules in a package.

Here is an example `database.py` module for your application::

    from sqlalchemy import create_engine, MetaData
    from sqlalchemy.orm import scoped_session, sessionmaker

    engine = create_engine('sqlite:////tmp/test.db', convert_unicode=True)
    metadata = MetaData()
    db_session = scoped_session(sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=engine))
    def init_db():
        metadata.create_all(bind=engine)

As for the declarative approach you need to close the session after
each request.  Put this into your application module::

    from yourapplication.database import db_session

    @app.teardown_request
    def shutdown_session(exception=None):
        db_session.remove()

Here is an example table and model (put this into `models.py`)::

    from sqlalchemy import Table, Column, Integer, String
    from sqlalchemy.orm import mapper
    from yourapplication.database import metadata, db_session

    class User(object):
        query = db_session.query_property()

        def __init__(self, name=None, email=None):
            self.name = name
            self.email = email

        def __repr__(self):
            return '<User %r>' % (self.name)

    users = Table('users', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String(50), unique=True),
        Column('email', String(120), unique=True)
    )
    mapper(User, users)

Querying and inserting works exactly the same as in the example above.


SQL Abstraction Layer
---------------------

If you just want to use the database system (and SQL) abstraction layer
you basically only need the engine::

    from sqlalchemy import create_engine, MetaData

    engine = create_engine('sqlite:////tmp/test.db', convert_unicode=True)
    metadata = MetaData(bind=engine)

Then you can either declare the tables in your code like in the examples
above, or automatically load them::

    users = Table('users', metadata, autoload=True)

To insert data you can use the `insert` method.  We have to get a
connection first so that we can use a transaction:

>>> con = engine.connect()
>>> con.execute(users.insert(), name='admin', email='admin@localhost')

SQLAlchemy will automatically commit for us.

To query your database, you use the engine directly or use a connection:

>>> users.select(users.c.id == 1).execute().first()
(1, u'admin', u'admin@localhost')

These results are also dict-like tuples:

>>> r = users.select(users.c.id == 1).execute().first()
>>> r['name']
u'admin'

You can also pass strings of SQL statements to the
:meth:`~sqlalchemy.engine.base.Connection.execute` method:

>>> engine.execute('select * from users where id = :1', [1]).first()
(1, u'admin', u'admin@localhost')

For more information about SQLAlchemy, head over to the
`website <http://sqlalchemy.org/>`_.
