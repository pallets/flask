.. _tutorial-views:

Step 5: The View Functions
==========================

Now that the database connections are working we can start writing the
view functions.  We will need four of them:

Show Entries
------------

This view shows all the entries stored in the database.  It listens on the
root of the application and will select title and text from the database.
The one with the highest id (the newest entry) will be on top.  The rows
returned from the cursor are tuples with the columns ordered like specified
in the select statement.  This is good enough for small applications like
here, but you might want to convert them into a dict.  If you are
interested in how to do that, check out the :ref:`easy-querying` example.

The view function will pass the entries as dicts to the
`show_entries.html` template and return the rendered one::

    @app.route('/')
    def show_entries():
        cur = g.db.execute('select title, text from entries order by id desc')
        entries = [dict(title=row[0], text=row[1]) for row in cur.fetchall()]
        return render_template('show_entries.html', entries=entries)

Add New Entry
-------------

This view lets the user add new entries if they are logged in.  This only
responds to `POST` requests, the actual form is shown on the
`show_entries` page.  If everything worked out well we will
:func:`~flask.flash` an information message to the next request and
redirect back to the `show_entries` page::

    @app.route('/add', methods=['POST'])
    def add_entry():
        if not session.get('logged_in'):
            abort(401)
        g.db.execute('insert into entries (title, text) values (?, ?)',
                     [request.form['title'], request.form['text']])
        g.db.commit()
        flash('New entry was successfully posted')
        return redirect(url_for('show_entries'))

Note that we check that the user is logged in here (the `logged_in` key is
present in the session and `True`).

.. admonition:: Security Note

   Be sure to use question marks when building SQL statements, as done in the
   example above.  Otherwise, your app will be vulnerable to SQL injection when
   you use string formatting to build SQL statements.
   See :ref:`sqlite3` for more.

Login and Logout
----------------

These functions are used to sign the user in and out.  Login checks the
username and password against the ones from the configuration and sets the
`logged_in` key in the session.  If the user logged in successfully, that
key is set to `True`, and the user is redirected back to the `show_entries`
page.  In addition, a message is flashed that informs the user that he or
she was logged in successfully.  If an error occurred, the template is
notified about that, and the user is asked again::

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        error = None
        if request.method == 'POST':
            if request.form['username'] != app.config['USERNAME']:
                error = 'Invalid username'
            elif request.form['password'] != app.config['PASSWORD']:
                error = 'Invalid password'
            else:
                session['logged_in'] = True
                flash('You were logged in')
                return redirect(url_for('show_entries'))
        return render_template('login.html', error=error)

The logout function, on the other hand, removes that key from the session
again.  We use a neat trick here: if you use the :meth:`~dict.pop` method
of the dict and pass a second parameter to it (the default), the method
will delete the key from the dictionary if present or do nothing when that
key is not in there.  This is helpful because now we don't have to check
if the user was logged in.

::

    @app.route('/logout')
    def logout():
        session.pop('logged_in', None)
        flash('You were logged out')
        return redirect(url_for('show_entries'))

Continue with :ref:`tutorial-templates`.
