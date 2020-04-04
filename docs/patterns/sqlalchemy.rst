SQLAlchemy in Flask
===================

Many people prefer `SQLAlchemy`_ for database access.  In this case it's
encouraged to use a package instead of a module for your flask application
and drop the models into a separate module (:doc:`packages`). While that
is not necessary, it makes a lot of sense.

There are four very common ways to use SQLAlchemy.  I will outline each
of them here:

Flask-SQLAlchemy Extension
--------------------------

Because SQLAlchemy is a common database abstraction layer and object
relational mapper that requires a little bit of configuration effort,
there is a Flask extension that handles that for you.  This is recommended
if you want to get started quickly.

You can download `Flask-SQLAlchemy`_ from `PyPI
<https://pypi.org/project/Flask-SQLAlchemy/>`_.

.. _Flask-SQLAlchemy: https://flask-sqlalchemy.palletsprojects.com/


Declarative
-----------

The declarative extension in SQLAlchemy is the most recent method of using
SQLAlchemy.  It allows you to define tables and models in one go, similar
to how Django works.  In addition to the following text I recommend the
official documentation on the `declarative`_ extension.

Here's the example :file:`database.py` module for your application::

    from sqlalchemy import create_engine
    from sqlalchemy.orm import scoped_session, sessionmaker
    from sqlalchemy.ext.declarative import declarative_base

    engine = create_engine('sqlite:////tmp/test.db')
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

To define your models, just subclass the `Base` class that was created by
the code above.  If you are wondering why we don't have to care about
threads here (like we did in the SQLite3 example above with the
:data:`~flask.g` object): that's because SQLAlchemy does that for us
already with the :class:`~sqlalchemy.orm.scoped_session`.

To use SQLAlchemy in a declarative way with your application, you just
have to put the following code into your application module.  Flask will
automatically remove database sessions at the end of the request or
when the application shuts down::

    from yourapplication.database import db_session

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

Here is an example model (put this into :file:`models.py`, e.g.)::

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
            return f'<User {self.name!r}>'

To create the database you can use the `init_db` function:

>>> from yourapplication.database import init_db
>>> init_db()

You can insert entries into the database like this:

>>> from yourapplication.database import db_session
>>> from yourapplication.models import User
>>> u = User('admin', 'admin@localhost')
>>> db_session.add(u)
>>> db_session.commit()

Querying is simple as well:

>>> User.query.all()
[<User 'admin'>]
>>> User.query.filter(User.name == 'admin').first()
<User 'admin'>

.. _SQLAlchemy: https://www.sqlalchemy.org/
.. _declarative: https://docs.sqlalchemy.org/en/latest/orm/extensions/declarative/

Manual Object Relational Mapping
--------------------------------

Manual object relational mapping has a few upsides and a few downsides
versus the declarative approach from above.  The main difference is that
you define tables and classes separately and map them together.  It's more
flexible but a little more to type.  In general it works like the
declarative approach, so make sure to also split up your application into
multiple modules in a package.

Here is an example :file:`database.py` module for your application::

    from sqlalchemy import create_engine, MetaData
    from sqlalchemy.orm import scoped_session, sessionmaker

    engine = create_engine('sqlite:////tmp/test.db')
    metadata = MetaData()
    db_session = scoped_session(sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=engine))
    def init_db():
        metadata.create_all(bind=engine)

As in the declarative approach, you need to close the session after
each request or application context shutdown.  Put this into your
application module::

    from yourapplication.database import db_session

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

Here is an example table and model (put this into :file:`models.py`)::

    from sqlalchemy import Table, Column, Integer, String
    from sqlalchemy.orm import mapper
    from yourapplication.database import metadata, db_session

    class User(object):
        query = db_session.query_property()

        def __init__(self, name=None, email=None):
            self.name = name
            self.email = email

        def __repr__(self):
            return f'<User {self.name!r}>'

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

    from sqlalchemy import create_engine, MetaData, Table

    engine = create_engine('sqlite:////tmp/test.db')
    metadata = MetaData(bind=engine)

Then you can either declare the tables in your code like in the examples
above, or automatically load them::

    from sqlalchemy import Table

    users = Table('users', metadata, autoload=True)

To insert data you can use the `insert` method.  We have to get a
connection first so that we can use a transaction:

>>> con = engine.connect()
>>> con.execute(users.insert(), name='admin', email='admin@localhost')

SQLAlchemy will automatically commit for us.

To query your database, you use the engine directly or use a connection:

>>> users.select(users.c.id == 1).execute().first()
(1, 'admin', 'admin@localhost')

These results are also dict-like tuples:

>>> r = users.select(users.c.id == 1).execute().first()
>>> r['name']
'admin'

You can also pass strings of SQL statements to the
:meth:`~sqlalchemy.engine.base.Connection.execute` method:

>>> engine.execute('select * from users where id = :1', [1]).first()
(1, 'admin', 'admin@localhost')

For more information about SQLAlchemy, head over to the
`website <https://www.sqlalchemy.org/>`_.
