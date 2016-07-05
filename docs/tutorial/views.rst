.. _tutorial-views:

Step 7: The View Functions
==========================

Now that the database connections are working, you can start writing the
view functions.  You will need four of them:

Show Entries
------------

This view shows all the entries stored in the database.  It listens on the
root of the application and will select title and text from the database.
The one with the highest id (the newest entry) will be on top.  The rows
returned from the cursor look a bit like dictionaries because we are using
the :class:`sqlite3.Row` row factory.

The view function will pass the entries to the :file:`show_entries.html`
template and return the rendered one::

    @app.route('/')
    def show_entries():
        db = get_db()
        cur = db.execute('select title, text from entries order by id desc')
        entries = cur.fetchall()
        return render_template('show_entries.html', entries=entries)

Add New Entry
-------------

This view lets the user add new entries if they are logged in.  This only
responds to ``POST`` requests; the actual form is shown on the
`show_entries` page.  If everything worked out well, it will
:func:`~flask.flash` an information message to the next request and
redirect back to the `show_entries` page::

    @app.route('/add', methods=['POST'])
    def add_entry():
        if not session.get('logged_in'):
            abort(401)
        db = get_db()
        db.execute('insert into entries (title, text) values (?, ?)',
                     [request.form['title'], request.form['text']])
        db.commit()
        flash('New entry was successfully posted')
        return redirect(url_for('show_entries'))

Note that this view checks that the user is logged in (that is, if the
`logged_in` key is present in the session and ``True``).

.. admonition:: Security Note

   Be sure to use question marks when building SQL statements, as done in the
   example above.  Otherwise, your app will be vulnerable to SQL injection when
   you use string formatting to build SQL statements.
   See :ref:`sqlite3` for more.

Login and Logout
----------------

These functions are used to sign the user in and out.  Login checks the
username and password against the ones from the configuration and sets the
`logged_in` key for the session.  If the user logged in successfully, that
key is set to ``True``, and the user is redirected back to the `show_entries`
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

The `logout` function, on the other hand, removes that key from the session
again.  There is a neat trick here: if you use the :meth:`~dict.pop` method
of the dict and pass a second parameter to it (the default), the method
will delete the key from the dictionary if present or do nothing when that
key is not in there.  This is helpful because now it is not necessary to
check if the user was logged in.

::

    @app.route('/logout')
    def logout():
        session.pop('logged_in', None)
        flash('You were logged out')
        return redirect(url_for('show_entries'))

.. admonition:: Security Note

    Passwords should never be stored in plain text in a production
    system. This tutorial uses plain text passwords for simplicity. If you
    plan to release a project based off this tutorial out into the world,
    passwords should be both `hashed and salted`_ before being stored in a
    database or file.

    Fortunately, there are Flask extensions for the purpose of
    hashing passwords and verifying passwords against hashes, so adding
    this functionality is fairly straight forward. There are also
    many general python libraries that can be used for hashing.

    You can find a list of recommended Flask extensions
    `here <http://flask.pocoo.org/extensions/>`_


Continue with :ref:`tutorial-templates`.

.. _hashed and salted: https://blog.codinghorror.com/youre-probably-storing-passwords-incorrectly/
