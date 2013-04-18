.. mongokit-pattern:

플라스크에서 MongoKit 사용하기
==============================

기능을 갖춘 DBMS 보다 문서 기반 데이터베이스를 사용하는 것이 요즘은 더 일반적이다.
이번 패턴은 MongoDB와 통합하기 위한 문서 매핑 라이브러리인 MongoKit의 사용법을 
보여준다.

이 패턴은 동작하는 MongoDB 서버와 MongoKit 라이브러리가 설치되있는 것을 전제로 한다.

MongoKit을 사용하는 두가지 일반적인 방식이 있다.  여기서 각 방법을 요약할 것이다:


선언 부분
---------

MongoKit의 기본 동작은 Django 나 SQLAlchemy의 선언적 확장의 공통 방식에 
기반을 둔 선언적 방식이다.

아래는 `app.py` 모듈의 예제이다::

    from flask import Flask
    from mongokit import Connection, Document

    # configuration
    MONGODB_HOST = 'localhost'
    MONGODB_PORT = 27017

    # create the little application object
    app = Flask(__name__)
    app.config.from_object(__name__)

    # connect to the database
    connection = Connection(app.config['MONGODB_HOST'],
                            app.config['MONGODB_PORT'])


여러분의 모델을 정의하기 위해, MongoKit에서 임포트한 `Document` 클래스는 상속해라.
SQLAlchemy 패턴을 봤다면 여러분은 왜 우리가 세션을 갖고 있지 않고 심지어
`init_db` 함수를 여기서 정의하지 않았는지 궁금해할 지도 모른다.  한편으로,
MongoKit은 세션같은 것을 갖지 않는다.  이것은 때때로 더 많이 타이핑을 하지만
엄청나게 빠르다. 다른 면으로, MongoDB는 스키마가 없다.  이것은 여러분이 
하나의 입력 질의로부터 어떤 문제도 없이 다음 질의에서 데이터 구조를 변경할 수 있다.
MongoKit 또한 스키마가 없지만, 데이터의 무결성을 보장하기 위해 어떤 검증을 구현한다.

여기서 예제 문서가 있다 (예를 들면 이것 또한 `app.py` 에 넣는다)::

    def max_length(length):
        def validate(value):
            if len(value) <= length:
                return True
            raise Exception('%s must be at most %s characters long' % length)
        return validate

    class User(Document):
        structure = {
            'name': unicode,
            'email': unicode,
        }
        validators = {
            'name': max_length(50),
            'email': max_length(120)
        }
        use_dot_notation = True
        def __repr__(self):
            return '<User %r>' % (self.name)

    # register the User document with our current connection
    connection.register([User])


이 예제는 여러분에게 스키마 (구조라 불리는) 를 정의하는 법, 최대 문자 길이에
대한 검증자를 보여주고 `use_dot_notation` 이라 불리는 특별한 MongoKit 기능을
사용한다.  기본 MongoKit 마다 파이썬 딕셔너리 같은 동작을 하지만 
`use_dot_notation` 에 `True` 로 설정을 하면 여러분은 속성들 사이를 분리하기
위해 점(dot)을 사용해서 어떤 다른 ORM과 근접한 모델을 사용하는 것 처럼 문서를
사용할 수 있다.

여러분은 아래 처럼 데이터베이스에 항목을 넣을 수 있다:

>>> from yourapplication.database import connection
>>> from yourapplication.models import User
>>> collection = connection['test'].users
>>> user = collection.User()
>>> user['name'] = u'admin'
>>> user['email'] = u'admin@localhost'
>>> user.save()

MongoKit은 사용된 컬럼 타입에 다소 엄격하고, 여러분은 유니코드인 `name` 또는 `email` 에 
대한 공통의 `str` 타입을 사용하지 않아야 한다. 

질의하는것 또한 간단하다:

>>> list(collection.User.find())
[<User u'admin'>]
>>> collection.User.find_one({'name': u'admin'})
<User u'admin'>

.. _MongoKit: http://bytebucket.org/namlook/mongokit/


PyMongo 호환성 계층
-------------------

여러분이 PyMongo를 단지 사용하고 싶다면, MongoKit을 가지고 그것을 할 수 있다.
여러분이 데이터를 얻는데 가장 좋은 성능이 필요하다면 이 프로세스를 사용하면 된다.
이 예제는 플라스크와 그것을 연결하는 방법을 보여주는지 않고, 예를 들면
위의 위의 MongoKit 코드를 봐라::

    from MongoKit import Connection

    connection = Connection()
데이터를 입력하기 위해 여러분은 `insert` 메소드를 사용할 수있다.  우리는 첫번째로
콜렉션을 얻어야하고, 이것은 SQL 세상에서 테이블과 약간 유사하다.

>>> collection = connection['test'].users
>>> user = {'name': u'admin', 'email': u'admin@localhost'}
>>> collection.insert(user)

MongoKit will automatically commit for us.

To query your database, you use the collection directly:

>>> list(collection.find())
[{u'_id': ObjectId('4c271729e13823182f000000'), u'name': u'admin', u'email': u'admin@localhost'}]
>>> collection.find_one({'name': u'admin'})
{u'_id': ObjectId('4c271729e13823182f000000'), u'name': u'admin', u'email': u'admin@localhost'}

These results are also dict-like objects:

>>> r = collection.find_one({'name': u'admin'})
>>> r['email']
u'admin@localhost'

For more information about MongoKit, head over to the
`website <https://github.com/namlook/mongokit>`_.
