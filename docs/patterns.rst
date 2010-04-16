.. _patterns:

Patterns for Flask
==================

Certain things are common enough that the changes are high you will find
them in most web applications.  For example quite a lot of applications
are using relational databases and user authentication.  In that case,
changes are they will open a database connection at the beginning of the
request and get the information of the currently logged in user.  At the
end of the request, the database connection is closed again.


.. _larger-applications:

Larger Applications
-------------------

For larger applications it's a good idea to use a package instead of a
module.  That is quite simple.  Imagine a small application looks like
this::

    /yourapplication
        /yourapplication.py
        /static
            /style.css
        /templates
            layout.html
            index.html
            login.html
            ...

To convert that into a larger one, just create a new folder
`yourapplication` inside the existing one and move everything below it.
Then rename `yourapplication.py` to `__init__.py`.  (Make sure to delete
all `.pyc` files first, otherwise things would most likely break)

You should then end up with something like that::

    /yourapplication
        /yourapplication
            /__init__.py
            /static
                /style.css
            /templates
                layout.html
                index.html
                login.html
                ...

But how do you run your application now?  The naive ``python
yourapplication/__init__.py`` will not work.  Let's just say that Python
does not want modules in packages to be the startup file.  But that is not
a big problem, just add a new file called `runserver.py` next to the inner
`yourapplication` folder with the following contents::

    from yourapplication import app
    app.run(debug=True)

What did we gain from this?  Now we can restructure the application a bit
into multiple modules.  The only thing you have to remember is the
following quick checklist:

1. the `Flask` application object creation have to be in the
   `__init__.py` file.  That way each module can import it safely and the
   `__name__` variable will resole to the correct package.
2. all the view functions (the ones with a :meth:`~flask.Flask.route`
   decorator on top) have to be imported when in the `__init__.py` file.
   Not the objects itself, but the module it is in.  Do the importing at
   the *bottom* of the file.

Here an example `__init__.py`::

    from flask import Flask
    app = Flask(__name__)

    import yourapplication.views

And this is what `views.py` would look like::

    from yourapplication import app

    @app.route('/')
    def index():
        return 'Hello World!'

.. admonition:: Circular Imports

   Every Python programmer hates it, and yet we just did that: circular
   imports (That's when two module depend on each one.  In this case
   `views.py` depends on `__init__.py`).  Be advised that this is a bad
   idea in general but here it is actually fine.  The reason for this is
   that we are not actually using the views in `__init__.py` and just
   ensuring the module is imported and we are doing that at the bottom of
   the file.

   There are still some problems with that approach but if you want to use
   decorators there is no way around that.  Check out the
   :ref:`becomingbig` section for some inspiration how to deal with that.


.. _database-pattern:

Using SQLite 3 with Flask
-------------------------

In Flask you can implement opening of dabase connections at the beginning
of the request and closing at the end with the
:meth:`~flask.Flask.before_request` and :meth:`~flask.Flask.after_request`
decorators in combination with the special :class:`~flask.g` object.

So here a simple example how you can use SQLite 3 with Flask::

    import sqlite3
    from flask import g

    DATABASE = '/path/to/database.db'

    def connect_db():
        return sqlite3.connect(DATABASE)

    @app.before_request
    def before_request():
        g.db = connect_db()

    @app.after_request
    def after_request(response):
        g.db.close()
        return response

.. _easy-querying:

Easy Querying
`````````````

Now in each request handling function you can access `g.db` to get the
current open database connection.  To simplify working with SQLite a
helper function can be useful::

    def query_db(query, args=(), one=False):
        cur = g.db.execute(query, args)
        rv = [dict((cur.description[idx][0], value)
                   for idx, value in enumerate(row)) for row in cur.fetchall()]
        return (rv[0] if rv else None) if one else rv

This handy little function makes working with the database much more
pleasant than it is by just using the raw cursor and connection objects.

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
the SQL statement with string formattings because this makes it possible
to attack the application using `SQL Injections
<http://en.wikipedia.org/wiki/SQL_injection>`_.

Initial Schemas
```````````````

Relational databases need schemas, so applications often ship a
`schema.sql` file that creates the database.  It's a good idea to provide
a function that creates the database bases on that schema.  This function
can do that for you::

    from contextlib import closing
    
    def init_db():
        with closing(connect_db()) as db:
            with app.open_resource('schema.sql') as f:
                db.cursor().executescript(f.read())
            db.commit()

You can then create such a database from the python shell:

>>> from yourapplication import init_db
>>> init_db()


.. _sqlalchemy-pattern:

SQLAlchemy in Flask
-------------------

Many people prefer `SQLAlchemy`_ for database access.  In this case it's
encouraged to use a package instead of a module for your flask application
and drop the models into a separate module (:ref:`larger-applications`).
Although that is not necessary but makes a lot of sense.

There are three very common ways to use SQLAlchemy.  I will outline each
of them here:

Declarative
```````````

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
````````````````````````````````

*coming soon*

SQL Abstraction Layer
`````````````````````

*coming soon*


.. _template-inheritance:

Template Inheritance
--------------------

The most powerful part of Jinja is template inheritance. Template inheritance
allows you to build a base "skeleton" template that contains all the common
elements of your site and defines **blocks** that child templates can override.

Sounds complicated but is very basic. It's easiest to understand it by starting
with an example.


Base Template
`````````````

This template, which we'll call ``layout.html``, defines a simple HTML skeleton
document that you might use for a simple two-column page. It's the job of
"child" templates to fill the empty blocks with content:

.. sourcecode:: html+jinja

    <!doctype html>
    <html>
      <head>
        {% block head %}
        <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
        <title>{% block title %}{% endblock %} - My Webpage</title>
        {% endblock %}
      </head>
    <body>
      <div id="content">{% block content %}{% endblock %}</div>
      <div id="footer">
        {% block footer %}
        &copy; Copyright 2010 by <a href="http://domain.invalid/">you</a>.
        {% endblock %}
      </div>
    </body>

In this example, the ``{% block %}`` tags define four blocks that child templates
can fill in. All the `block` tag does is to tell the template engine that a
child template may override those portions of the template.

Child Template
``````````````

A child template might look like this:

.. sourcecode:: html+jinja

    {% extends "layout.html" %}
    {% block title %}Index{% endblock %}
    {% block head %}
      {{ super() }}
      <style type="text/css">
        .important { color: #336699; }
      </style>
    {% endblock %}
    {% block content %}
      <h1>Index</h1>
      <p class="important">
        Welcome on my awesome homepage.
    {% endblock %}

The ``{% extends %}`` tag is the key here. It tells the template engine that
this template "extends" another template.  When the template system evaluates
this template, first it locates the parent.  The extends tag must be the
first tag in the template.  To render the contents of a block defined in
the parent template, use ``{{ super() }}``.

.. _message-flashing-pattern:

Message Flashing
----------------

Good applications and user interfaces are all about feedback.  If the user
does not get enough feedback he will probably end up hating the
application.  Flask provides a really simple way to give feedback to a
user with the flashing system.  The flashing system basically makes it
possible to record a message at the end of a request and access it next
request and only next request.  This is usually combined with a layout
template that does this.

So here a full example::

    from flask import flash, redirect, url_for, render_template

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        error = None
        if request.method == 'POST':
            if request.form['username'] != 'admin' or \
               request.form['password'] != 'secret':
                error = 'Invalid credentials'
            else:
                flash('You were sucessfully logged in')
                return redirect(url_for('index'))
        return render_template('login.html', error=error)

And here the ``layout.html`` template which does the magic:

.. sourcecode:: html+jinja

   <!doctype html>
   <title>My Application</title>
   {% with messages = get_flashed_messages() %}
     {% if messages %}
       <ul class=flashes>
       {% for message in messages %}
         <li>{{ message }}</li>
       {% endfor %}
       </ul>
     {% endif %}
   {% endwith %}
   {% block body %}{% endblock %}

And here the index.html template:

.. sourcecode:: html+jinja

   {% extends "layout.html" %}
   {% block body %}
     <h1>Overview</h1>
     <p>Do you want to <a href="{{ url_for('login') }}">log in?</a>
   {% endblock %}

And of course the login template:

.. sourcecode:: html+jinja

   {% extends "layout.html" %}
   {% block body %}
     <h1>Login</h1>
     {% if error %}
       <p class=error><strong>Error:</strong> {{ error }}
     {% endif %}
     <form action="" method=post>
       <dl>
         <dt>Username:
         <dd><input type=text name=username value="{{
             request.form.username }}">
         <dt>Password:
         <dd><input type=password name=password>
       </dl>
       <p><input type=submit value=Login>
     </form>
   {% endblock %}
