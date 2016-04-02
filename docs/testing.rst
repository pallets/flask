.. _testing:

Testing Flask Applications
==========================

   **Something that is untested is broken.**

The origin of this quote is unknown and while it is not entirely correct, it is also
not far from the truth.  Untested applications make it hard to
improve existing code and developers of untested applications tend to
become pretty paranoid.  If an application has automated tests, you can
safely make changes and instantly know if anything breaks.

Flask provides a way to test your application by exposing the Werkzeug
test :class:`~werkzeug.test.Client` and handling the context locals for you.
You can then use that with your favourite testing solution.  In this documentation
we will use the :mod:`unittest` package that comes pre-installed with Python.

The Application
---------------

First, we need an application to test; we will use the application from
the :ref:`tutorial`.  If you don't have that application yet, get the
sources from `the examples`_.

.. _the examples:
   https://github.com/pallets/flask/tree/master/examples/flaskr/

The Testing Skeleton
--------------------

In order to test the application, we add a second module
(:file:`flaskr_tests.py`) and create a unittest skeleton there::

    import os
    import flaskr
    import unittest
    import tempfile

    class FlaskrTestCase(unittest.TestCase):

        def setUp(self):
            self.db_fd, flaskr.app.config['DATABASE'] = tempfile.mkstemp()
            flaskr.app.config['TESTING'] = True
            self.app = flaskr.app.test_client()
            with flaskr.app.app_context():
                flaskr.init_db()

        def tearDown(self):
            os.close(self.db_fd)
            os.unlink(flaskr.app.config['DATABASE'])

    if __name__ == '__main__':
        unittest.main()

The code in the :meth:`~unittest.TestCase.setUp` method creates a new test
client and initializes a new database.  This function is called before
each individual test function is run.  To delete the database after the
test, we close the file and remove it from the filesystem in the
:meth:`~unittest.TestCase.tearDown` method.  Additionally during setup the
``TESTING`` config flag is activated.  What it does is disable the error
catching during request handling so that you get better error reports when
performing test requests against the application.

This test client will give us a simple interface to the application.  We can
trigger test requests to the application, and the client will also keep track
of cookies for us.

Because SQLite3 is filesystem-based we can easily use the tempfile module
to create a temporary database and initialize it.  The
:func:`~tempfile.mkstemp` function does two things for us: it returns a
low-level file handle and a random file name, the latter we use as
database name.  We just have to keep the `db_fd` around so that we can use
the :func:`os.close` function to close the file.

If we now run the test suite, we should see the following output::

    $ python flaskr_tests.py

    ----------------------------------------------------------------------
    Ran 0 tests in 0.000s

    OK

Even though it did not run any actual tests, we already know that our flaskr
application is syntactically valid, otherwise the import would have died
with an exception.

The First Test
--------------

Now it's time to start testing the functionality of the application.
Let's check that the application shows "No entries here so far" if we
access the root of the application (``/``). To do this, we add a new
test method to our class, like this::

    class FlaskrTestCase(unittest.TestCase):

        def setUp(self):
            self.db_fd, flaskr.app.config['DATABASE'] = tempfile.mkstemp()
            self.app = flaskr.app.test_client()
            flaskr.init_db()

        def tearDown(self):
            os.close(self.db_fd)
            os.unlink(flaskr.app.config['DATABASE'])

        def test_empty_db(self):
            rv = self.app.get('/')
            assert b'No entries here so far' in rv.data

Notice that our test functions begin with the word `test`; this allows
:mod:`unittest` to automatically identify the method as a test to run.

By using `self.app.get` we can send an HTTP ``GET`` request to the application with
the given path.  The return value will be a :class:`~flask.Flask.response_class` object.
We can now use the :attr:`~werkzeug.wrappers.BaseResponse.data` attribute to inspect
the return value (as string) from the application.  In this case, we ensure that
``'No entries here so far'`` is part of the output.

Run it again and you should see one passing test::

    $ python flaskr_tests.py
    .
    ----------------------------------------------------------------------
    Ran 1 test in 0.034s

    OK

Logging In and Out
------------------

The majority of the functionality of our application is only available for
the administrative user, so we need a way to log our test client in and out
of the application.  To do this, we fire some requests to the login and logout
pages with the required form data (username and password).  And because the
login and logout pages redirect, we tell the client to `follow_redirects`.

Add the following two methods to your `FlaskrTestCase` class::

   def login(self, username, password):
       return self.app.post('/login', data=dict(
           username=username,
           password=password
       ), follow_redirects=True)

   def logout(self):
       return self.app.get('/logout', follow_redirects=True)

Now we can easily test that logging in and out works and that it fails with
invalid credentials.  Add this new test to the class::

   def test_login_logout(self):
       rv = self.login('admin', 'default')
       assert 'You were logged in' in rv.data
       rv = self.logout()
       assert 'You were logged out' in rv.data
       rv = self.login('adminx', 'default')
       assert 'Invalid username' in rv.data
       rv = self.login('admin', 'defaultx')
       assert 'Invalid password' in rv.data

Test Adding Messages
--------------------

We should also test that adding messages works.  Add a new test method
like this::

    def test_messages(self):
        self.login('admin', 'default')
        rv = self.app.post('/add', data=dict(
            title='<Hello>',
            text='<strong>HTML</strong> allowed here'
        ), follow_redirects=True)
        assert 'No entries here so far' not in rv.data
        assert '&lt;Hello&gt;' in rv.data
        assert '<strong>HTML</strong> allowed here' in rv.data

Here we check that HTML is allowed in the text but not in the title,
which is the intended behavior.

Running that should now give us three passing tests::

    $ python flaskr_tests.py
    ...
    ----------------------------------------------------------------------
    Ran 3 tests in 0.332s

    OK

For more complex tests with headers and status codes, check out the
`MiniTwit Example`_ from the sources which contains a larger test
suite.


.. _MiniTwit Example:
   https://github.com/pallets/flask/tree/master/examples/minitwit/


Other Testing Tricks
--------------------

Besides using the test client as shown above, there is also the
:meth:`~flask.Flask.test_request_context` method that can be used
in combination with the ``with`` statement to activate a request context
temporarily.  With this you can access the :class:`~flask.request`,
:class:`~flask.g` and :class:`~flask.session` objects like in view
functions.  Here is a full example that demonstrates this approach::

    import flask
    
    app = flask.Flask(__name__)

    with app.test_request_context('/?name=Peter'):
        assert flask.request.path == '/'
        assert flask.request.args['name'] == 'Peter'

All the other objects that are context bound can be used in the same
way.

If you want to test your application with different configurations and
there does not seem to be a good way to do that, consider switching to
application factories (see :ref:`app-factories`).

Note however that if you are using a test request context, the
:meth:`~flask.Flask.before_request` and :meth:`~flask.Flask.after_request`
functions are not called automatically.  However
:meth:`~flask.Flask.teardown_request` functions are indeed executed when
the test request context leaves the ``with`` block.  If you do want the
:meth:`~flask.Flask.before_request` functions to be called as well, you
need to call :meth:`~flask.Flask.preprocess_request` yourself::

    app = flask.Flask(__name__)

    with app.test_request_context('/?name=Peter'):
        app.preprocess_request()
        ...

This can be necessary to open database connections or something similar
depending on how your application was designed.

If you want to call the :meth:`~flask.Flask.after_request` functions you
need to call into :meth:`~flask.Flask.process_response` which however
requires that you pass it a response object::

    app = flask.Flask(__name__)

    with app.test_request_context('/?name=Peter'):
        resp = Response('...')
        resp = app.process_response(resp)
        ...

This in general is less useful because at that point you can directly
start using the test client.

.. _faking-resources:

Faking Resources and Context
----------------------------

.. versionadded:: 0.10

A very common pattern is to store user authorization information and
database connections on the application context or the :attr:`flask.g`
object.  The general pattern for this is to put the object on there on
first usage and then to remove it on a teardown.  Imagine for instance
this code to get the current user::

    def get_user():
        user = getattr(g, 'user', None)
        if user is None:
            user = fetch_current_user_from_database()
            g.user = user
        return user

For a test it would be nice to override this user from the outside without
having to change some code.  This can be accomplished with
hooking the :data:`flask.appcontext_pushed` signal::

    from contextlib import contextmanager
    from flask import appcontext_pushed, g

    @contextmanager
    def user_set(app, user):
        def handler(sender, **kwargs):
            g.user = user
        with appcontext_pushed.connected_to(handler, app):
            yield

And then to use it::

    from flask import json, jsonify

    @app.route('/users/me')
    def users_me():
        return jsonify(username=g.user.username)

    with user_set(app, my_user):
        with app.test_client() as c:
            resp = c.get('/users/me')
            data = json.loads(resp.data)
            self.assert_equal(data['username'], my_user.username)


Keeping the Context Around
--------------------------

.. versionadded:: 0.4

Sometimes it is helpful to trigger a regular request but still keep the
context around for a little longer so that additional introspection can
happen.  With Flask 0.4 this is possible by using the
:meth:`~flask.Flask.test_client` with a ``with`` block::

    app = flask.Flask(__name__)

    with app.test_client() as c:
        rv = c.get('/?tequila=42')
        assert request.args['tequila'] == '42'

If you were to use just the :meth:`~flask.Flask.test_client` without
the ``with`` block, the ``assert`` would fail with an error because `request`
is no longer available (because you are trying to use it outside of the actual request).


Accessing and Modifying Sessions
--------------------------------

.. versionadded:: 0.8

Sometimes it can be very helpful to access or modify the sessions from the
test client.  Generally there are two ways for this.  If you just want to
ensure that a session has certain keys set to certain values you can just
keep the context around and access :data:`flask.session`::

    with app.test_client() as c:
        rv = c.get('/')
        assert flask.session['foo'] == 42

This however does not make it possible to also modify the session or to
access the session before a request was fired.  Starting with Flask 0.8 we
provide a so called “session transaction” which simulates the appropriate
calls to open a session in the context of the test client and to modify
it.  At the end of the transaction the session is stored.  This works
independently of the session backend used::

    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess['a_key'] = 'a value'

        # once this is reached the session was stored

Note that in this case you have to use the ``sess`` object instead of the
:data:`flask.session` proxy.  The object however itself will provide the
same interface.
