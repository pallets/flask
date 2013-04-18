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
If you've seen the SQLAlchemy pattern you may wonder why we do
not have a session and even do not define a `init_db` function here.  On the
one hand, MongoKit does not have something like a session.  This sometimes
makes it more to type but also makes it blazingly fast.  On the other hand,
MongoDB is schemaless.  This means you can modify the data structure from one
insert query to the next without any problem.  MongoKit is just schemaless
too, but implements some validation to ensure data integrity.

Here is an example document (put this also into `app.py`, e.g.)::

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


This example shows you how to define your schema (named structure), a
validator for the maximum character length and uses a special MongoKit feature
called `use_dot_notation`.  Per default MongoKit behaves like a python
dictionary but with `use_dot_notation` set to `True` you can use your
documents like you use models in nearly any other ORM by using dots to
separate between attributes.

You can insert entries into the database like this:

>>> from yourapplication.database import connection
>>> from yourapplication.models import User
>>> collection = connection['test'].users
>>> user = collection.User()
>>> user['name'] = u'admin'
>>> user['email'] = u'admin@localhost'
>>> user.save()

Note that MongoKit is kinda strict with used column types, you must not use a
common `str` type for either `name` or `email` but unicode.

Querying is simple as well:

>>> list(collection.User.find())
[<User u'admin'>]
>>> collection.User.find_one({'name': u'admin'})
<User u'admin'>

.. _MongoKit: http://bytebucket.org/namlook/mongokit/


PyMongo Compatibility Layer
---------------------------

If you just want to use PyMongo, you can do that with MongoKit as well.  You
may use this process if you need the best performance to get.  Note that this
example does not show how to couple it with Flask, see the above MongoKit code
for examples::

    from MongoKit import Connection

    connection = Connection()

To insert data you can use the `insert` method.  We have to get a
collection first, this is somewhat the same as a table in the SQL world.

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
