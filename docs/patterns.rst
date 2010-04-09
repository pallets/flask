.. _patterns:

Patterns in Flask
=================

Certain things are common enough that the changes are high you will find
them in most web applications.  For example quite a lot of applications
are using relational databases and user authentication.  In that case,
changes are they will open a database connection at the beginning of the
request and get the information of the currently logged in user.  At the
end of the request, the database connection is closed again.

In Flask you can implement such things with the
:meth:`~flask.Flask.request_init` and
:meth:`~flask.Flask.request_shutdown` decorators in combination with the
special :class:`~flask.g` object.


Using SQLite 3 with Flask
-------------------------

So here a simple example how you can use SQLite 3 with Flask::

    import sqlite3
    from flask import g

    DATABASE = '/path/to/database.db'

    def connect_db():
        return sqlite3.connect(DATABASE)

    @app.request_init
    def before_request():
        g.db = connect_db()

    @app.request_shutdown
    def after_request(response):
        g.db.close()
        return response

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
