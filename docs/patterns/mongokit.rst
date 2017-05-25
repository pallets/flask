.. mongokit-pattern:

MongoKit in Flask
=================

Using a document database rather than a full DBMS gets more common these days.
This pattern shows how to use MongoKit, a document mapper library, to
integrate with MongoDB.

This pattern requires a running MongoDB server and the MongoKit library
installed.

There are two very common ways to use MongoKit.  I will outline each of them
here:


Declarative
-----------

The default behavior of MongoKit is the declarative one that is based on
common ideas from Django or the SQLAlchemy declarative extension.

Here an example :file:`app.py` module for your application::

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


To define your models, just subclass the `Document` class that is imported
from MongoKit.  If you've seen the SQLAlchemy pattern you may wonder why we do
not have a session and even do not define a `init_db` function here.  On the
one hand, MongoKit does not have something like a session.  This sometimes
makes it more to type but also makes it blazingly fast.  On the other hand,
MongoDB is schemaless.  This means you can modify the data structure from one
insert query to the next without any problem.  MongoKit is just schemaless
too, but implements some validation to ensure data integrity.

Here is an example document (put this also into :file:`app.py`, e.g.)::

    from mongokit import ValidationError

    def max_length(length):
        def validate(value):
            if len(value) <= length:
                return True
            # must have %s in error format string to have mongokit place key in there
            raise ValidationError('%s must be at most {} characters long'.format(length))
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
dictionary but with `use_dot_notation` set to ``True`` you can use your
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
