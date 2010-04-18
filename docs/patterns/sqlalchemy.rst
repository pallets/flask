.. _sqlalchemy-pattern:

SQLAlchemy in Flask
===================

Many people prefer `SQLAlchemy`_ for database access.  In this case it's
encouraged to use a package instead of a module for your flask application
and drop the models into a separate module (:ref:`larger-applications`).
Although that is not necessary but makes a lot of sense.

There are three very common ways to use SQLAlchemy.  I will outline each
of them here:

Declarative
-----------

The declarative extension in SQLAlchemy is the most recent method of using
SQLAlchemy.  It allows you to define tables and models in one go, similar
to how Django works.  In addition to the following text I recommend the
official documentation on the `declarative`_ extension.

Here the example `database.py` module for your application::

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
        Base.metadata.create_all(bind=engine)

To define your models, just subclass the `Base` class that was created by
the code above.  If you are wondering why we don't have to care about
threads here (like we did in the SQLite3 example above with the
:data:`~flask.g` object): that's because SQLAlchemy does that for us
already with the :class:`~sqlalchemy.orm.scoped_session`.

To use SQLAlchemy in a declarative way with your application, you just
have to put the following code into your application module.  Flask will
automatically remove database sessions at the end of the request for you::

    from yourapplication.database import db_session

    @app.after_request
    def shutdown_session(response):
        db_session.remove()
        return response

Here an example model (put that into `models.py` for instance)::

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
            return '<User %r>' % (self.name, self.email)

You can insert entries into the database like this then:

>>> from yourapplication.database import db_session
>>> from yourapplication.models import User
>>> u = User('admin', 'admin@localhost')
>>> db_session.add(u)
>>> db_session.commit()

Querying is simple as well:

>>> User.query.all()
[<User u'admin'>]
>>> User.query.filter(User.name == 'admin').first()
<User u'admin'>

.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _declarative:
   http://www.sqlalchemy.org/docs/reference/ext/declarative.html

Manual Object Relational Mapping
--------------------------------

*coming soon*

SQL Abstraction Layer
---------------------

*coming soon*
