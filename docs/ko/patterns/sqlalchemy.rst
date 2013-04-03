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
`Flask-SQLAlchemy`_ 를 받을 수 있다. 

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

수동 객체 관계 매핑
-------------------

수동 객체 관계 매핑은 앞에서 나온 선언적 접근에 대비하여 몇 가지 
장단점을 갖는다.  주요한 차이점은 여러분이 테이블들과 클래스들을
분리해서 정의하고 그것들을 함께 매핑한다는 것이다.  그 방식은 
더 유연하지만 입력할 것이 약간 더 있다.  일반적으로 선언적 접근처럼
동작하기 때문에 어려분의 어플리케이션 또한 패키지안에 여러 모듈로
분리되도록 보장해라.

여기 여러분의 어플리케이션에 대한 `database.py` 모듈의 예가 있다::

    from sqlalchemy import create_engine, MetaData
    from sqlalchemy.orm import scoped_session, sessionmaker

    engine = create_engine('sqlite:////tmp/test.db', convert_unicode=True)
    metadata = MetaData()
    db_session = scoped_session(sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=engine))
    def init_db():
        metadata.create_all(bind=engine)

선언적 접근법에 대하여 여러분은 각 요청 후에 세션을 닫을 필요가 있다.
이것을 여러분의 어플리케이션 모듈에 넣어라::

    from yourapplication.database import db_session

    @app.teardown_request
    def shutdown_session(exception=None):
        db_session.remove()

여기에 예제 테이블과 모델이 있다 (이것을 `models.py` 에 넣어라)::

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

질의하고 추가하는 것은 위의 예제에서와 정확히 같게 동작한다.


SQL 추상 계층
-------------

여러분이 단지 데이타베이스 시스템 (그리고 SQL) 추상 계층을 사용하고 싶다면
여러분은 기본적으로 단지 그 엔진만 필요한 것이다::

    from sqlalchemy import create_engine, MetaData

    engine = create_engine('sqlite:////tmp/test.db', convert_unicode=True)
    metadata = MetaData(bind=engine)

그러면 여러분은 위의 예제에서 처럼 여러분의 코드에 테이블을 선언할 수 있거나,
자동으로 그것들을 적재할 수 있다::

    users = Table('users', metadata, autoload=True)

데이타를 추가하기 위해서 여러분은 `insert` 메소드를 사용할 수 있다.
우리는 트랜젝션을 사용할 수 있도록 먼저 연결을 얻어야 한다:

>>> con = engine.connect()
>>> con.execute(users.insert(), name='admin', email='admin@localhost')

SQLAlchemy는 자동으로 커밋을 할 것이다.

여러분의 데이타베이스에 질의하기 위해서, 여러분은 직접 엔진을 사용하거나
트랜잭션을 사용한다.

>>> users.select(users.c.id == 1).execute().first()
(1, u'admin', u'admin@localhost')

이런 결과들 또한 딕셔너리와 같은 튜플이다::

>>> r = users.select(users.c.id == 1).execute().first()
>>> r['name']
u'admin'

여러분은 또한 :meth:`~sqlalchemy.engine.base.Connection.execute` 메소드에 
SQL 구문의 문자열을 넘길 수 있다.:

>>> engine.execute('select * from users where id = :1', [1]).first()
(1, u'admin', u'admin@localhost')

SQLAlchemy에 대해서 더 많은 정보는 `website <http://sqlalchemy.org/>`_ 로
넘어가면 된다.
