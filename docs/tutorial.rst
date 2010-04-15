.. _tutorial:

Tutorial
========

You want to develop an application with Python and Flask?  Here you have
the chance to learn that by example.  In this tutorial we will create a
simple microblog application.  It only supports one user that can create
text-only entries and there are no feeds or comments, but it still
features everything you need to get started.  We will use Flask and SQLite
as database which comes out of the box with Python, so there is nothing
else you need.

If you want the full sourcecode in advance or for comparison, check out
the `example source`_.

.. _example source:
   http://github.com/mitsuhiko/flask/tree/master/examples/flaskr/

Introducing Flaskr
------------------

We will call our blogging application flaskr here, feel free to chose a
less web-2.0-ish name ;)  Basically we want it to do the following things:

1. let the user sign in and out with credentials specified in the
   configuration.  Only one user is supported.
2. when the user is logged in he or she can add new entries to the page
   consisting of a text-only title and some HTML for the text.  This HTML
   is not sanitized because we trust the user here.
3. the page shows all entries so far in reverse order (newest on top) and
   the user can add new ones from there if logged in.

Here a screenshot from the final application:

.. image:: _static/flaskr.png
   :align: center
   :class: screenshot
   :alt: screenshot of the final application

Step 0: Creating The Folders
----------------------------

Before we get started, let's create the folders needed for this
application::

    /flaskr
        /static
        /templates

The `flaskr` folder is not a python package, but just something where we
drop our files.  Directly into this folder we will then put our database
schema as well as main module in the following steps.

Step 1: Database Schema
-----------------------

First we want to create the database schema.  For this application only a
single table is needed and we only want to support SQLite so that is quite
easy.  Just put the following contents into a file named `schema.sql` in
the just created `flaskr` folder:

.. sourcecode:: sql

    drop table if exists entries;
    create table entries (
      id integer primary key autoincrement,
      title string not null,
      text string not null
    );

This schema consists of a single table called `entries` and each row in
this table has an `id`, a `title` and a `text`.  The `id` is an
automatically incrementing integer and a primary key, the other two are
strings that must not be null.

Step 2: Application Setup Code
------------------------------

Now that we have the schema in place we can create the application module.
Let's call it `flaskr.py` inside the `flaskr` folder.  For starters we
will add the imports we will need as well as the config section::

    # all the imports
    import sqlite3
    from flask import Flask, request, session, g, redirect, url_for, abort, \
         render_template, flash

    # configuration
    DATABASE = '/tmp/flaskr.db'
    DEBUG = True
    SECRET_KEY = 'development key'
    USERNAME = 'admin'
    PASSWORD = 'default'

The `with_statement` and :func:`~contextlib.closing` function are used to
make dealing with the database connection easier later on for setting up
the initial database.  Next we can create our actual application and
initialize it with the config::

    # create our little application :)
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    app.debug = DEBUG

We can also add a method to easily connect to the database sepcified::

    def connect_db():
        return sqlite3.connect(DATABASE)

Finally we just add a line to the bottom of the file that fires up the
server if we run that file as standalone application::

    if __name__ == '__main__':
        app.run()

.. admonition:: Troubleshooting

   If you notice later that the browser cannot connect to the server
   during development, you might want to try this line instead::

       app.run(host='127.0.0.1')

   In a nutshell: Werkzeug starts up as IPv6 on many operating systems by
   default and not every browser is happy with that.  This forces IPv4
   usage.

With that out of the way you should be able to start up the application
without problems.  When you head over to the server you will get an 404
page not found error because we don't have any views yet.  But we will
focus on that a little later.  First we should get the database working.

Step 3: Creating The Database
-----------------------------

Flaskr is a database powered application as outlined earlier, and more
precisely, an application powered by a relational database system.  Such
systems need a schema that tells them how to store that information. So
before starting the server for the first time it's important to create
that schema.

Such a schema can be created by piping the `schema.sql` file into the
`sqlite3` command as follows::

    sqlite3 /tmp/flaskr.db < schema.sql

The downside of this is that it requires the sqlite3 command to be
installed which is not necessarily the case on every system.  Also one has
to provide the path to the database there which leaves some place for
errors.  It's a good idea to add a function that initializes the database
for you to the application.

If you want to do that, you first have to import the
:func:`contextlib.closing` function from the contextlib package.  If you
want to use Python 2.5 it's also necessary to enable the `with` statement
first (`__future__` imports must be the very first import)::

    from __future__ import with_statement
    from contextlib import closing

Next we can create a function called `init_db` that initializes the
database::
    
    def init_db():
        with closing(connect_db()) as db:
            with app.open_resource('schema.sql') as f:
                db.cursor().executescript(f.read())
            db.commit()

Now it is possible to create a database by starting up a Python shell and
importing and calling that function::

>>> from flaskr import init_db
>>> init_db()

The :meth:`~flask.Flask.open_resource` function opens a file from the
resource location (your flaskr folder) and allows you to read from it.  We
are using this here to execute a script on the database connection.

When we connect to a database we get a connection object (here called
`db`) that can give us a cursor.  On that cursor there is a method to
execute a complete script.  Finally we only have to commit the changes and
close the transaction.

Step 4: Request Database Connections
------------------------------------

Now we know how we can open database connections and use them for scripts,
but how can we elegantly do that for requests?  We will need the database
connection in all our functions so it makes sense to initialize them
before each request and shut them down afterwards.

Flask allows us to do that with the :meth:`~flask.Flask.request_init` and
:meth:`~flask.Flask.request_shutdown` decorators::

    @app.request_init
    def before_request():
        g.db = connect_db()

    @app.request_shutdown
    def after_request(response):
        g.db.close()
        return response

Functions marked with :meth:`~flask.Flask.request_init` are called before
a request and passed no arguments, functions marked with
:meth:`~flask.Flask.request_shutdown` are called after a request and
passed the response that will be sent to the client.  They have to return
that response object or a different one.  In this case we just return it
unchanged.

We store our current database connection on the special :data:`~flask.g`
object that flask provides for us.  This object stores information for one
request only and is available from within each function.  Never store such
things on other objects because this would not work with threaded
environments.  That special :data:`~flask.g` object does some magic behind
the scenes to ensure it does the right thing.

Step 5: The View Functions
--------------------------

Now that the database connections are working we can start writing the
view functions.  We will need for of them:

Show Entries
````````````

This view shows all the entries stored in the database::

    @app.route('/')
    def show_entries():
        cur = g.db.execute('select title, text from entries order by id desc')
        entries = [dict(title=row[0], text=row[1]) for row in cur.fetchall()]
        return render_template('show_entries.html', entries=entries)

Add New Entry
`````````````

This view lets the user add new entries if he's logged in.  This only
responds to `POST` requests, the actual form is shown on the
`show_entries` page::

    @app.route('/add', methods=['POST'])
    def add_entry():
        if not session.get('logged_in'):
            abort(401)
        g.db.execute('insert into entries (title, text) values (?, ?)',
                     [request.form['title'], request.form['text']])
        g.db.commit()
        flash('New entry was successfully posted')
        return redirect(url_for('show_entries'))

Login and Logout
````````````````

These functions are used to sign the user in and out::

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        error = None
        if request.method == 'POST':
            if request.form['username'] != USERNAME:
                error = 'Invalid username'
            elif request.form['password'] != PASSWORD:
                error = 'Invalid password'
            else:
                session['logged_in'] = True
                flash('You were logged in')
                return redirect(url_for('show_entries'))
        return render_template('login.html', error=error)

    @app.route('/logout')
    def logout():
        session.pop('logged_in', None)
        flash('You were logged out')
        return redirect(url_for('show_entries'))

Step 6: The Templates
---------------------

Now we should start working on the templates.  If we request the URLs now
we would only get an exception that Flask cannot find the templates.

Put the following templates into the `templates` folder:

layout.html
```````````

.. sourcecode:: html+jinja

    <!doctype html>
    <title>Flaskr</title>
    <link rel=stylesheet type=text/css href="{{ url_for('static', filename='style.css') }}">
    <div class=page>
      <h1>Flaskr</h1>
      <div class=metanav>
      {% if not session.logged_in %}
        <a href="{{ url_for('login') }}">log in</a>
      {% else %}
        <a href="{{ url_for('logout') }}">log out</a>
      {% endif %}
      </div>
      {% for message in get_flashed_messages() %}
        <div class=flash>{{ message }}</div>
      {% endfor %}
      {% block body %}{% endblock %}
    </div>

show_entries.html
`````````````````

.. sourcecode:: html+jinja

    {% extends "layout.html" %}
    {% block body %}
      {% if g.logged_in %}
        <form action="{{ url_for('add_entry') }}" method=post class=add-entry>
          <dl>
            <dt>Title:
            <dd><input type=text size=30 name=title>
            <dt>Text:
            <dd><textarea name=text rows=5 cols=40></textarea>
            <dd><input type=submit value=Share>
          </dl>
        </form>
      {% endif %}
      <ul class=entries>
      {% for entry in entries %}
        <li><h2>{{ entry.title }}</h2>{{ entry.text|safe }}
      {% else %}
        <li><em>Unbelievable.  No entries here so far</em>
      {% endfor %}
      </ul>
    {% endblock %}

login.html
``````````

.. sourcecode:: html+jinja

    {% extends "layout.html" %}
    {% block body %}
      <h2>Login</h2>
      {% if error %}<p class=error><strong>Error:</strong> {{ error }}{% endif %}
      <form action="{{ url_for('login') }}" method=post>
        <dl>
          <dt>Username:
          <dd><input type=text name=username>
          <dt>Password:
          <dd><input type=password name=password>
          <dd><input type=submit value=Login>
        </dl>
      </form>
    {% endblock %}
