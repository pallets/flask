.. _testing:

Testing Flask Applications
==========================

   **Something that is untested is broken.**

Not sure where that is coming from, and it's not entirely correct, but
also not that far from the truth.  Untested applications make it hard to
improve existing code and developers of untested applications tend to
become pretty paranoid.  If an application has automated tests, you can
safely change things, and you will instantly know if your change broke
something.

Flask gives you a couple of ways to test applications.  It mainly does
that by exposing the Werkzeug test :class:`~werkzeug.Client` class to your
code and handling the context locals for you.  You can then use that with
your favourite testing solution.  In this documentation we will use the
:mod:`unittest` package that comes preinstalled with each Python
installation.

The Application
---------------

First we need an application to test for functionality.  For the testing
we will use the application from the :ref:`tutorial`.  If you don't have
that application yet, get the sources from `the examples`_.

.. _the examples:
   http://github.com/mitsuhiko/flask/tree/master/examples/flaskr/

The Testing Skeleton
--------------------

In order to test that, we add a second module (
`flaskr_tests.py`) and create a unittest skeleton there::

    import os
    import flaskr
    import unittest
    import tempfile

    class FlaskrTestCase(unittest.TestCase):

        def setUp(self):
            self.db_fd, flaskr.DATABASE = tempfile.mkstemp()
            self.app = flaskr.app.test_client()
            flaskr.init_db()

        def tearDown(self):
            os.close(self.db_fd)
            os.unlink(flaskr.DATABASE)

    if __name__ == '__main__':
        unittest.main()

The code in the :meth:`~unittest.TestCase.setUp` method creates a new test
client and initializes a new database.  That function is called before
each individual test function.  To delete the database after the test, we
close the file and remove it from the filesystem in the
:meth:`~unittest.TestCase.tearDown` method.  What the test client does is
give us a simple interface to the application.  We can trigger test
requests to the application, and the client will also keep track of cookies
for us.

Because SQLite3 is filesystem-based we can easily use the tempfile module
to create a temporary database and initialize it.  The
:func:`~tempfile.mkstemp` function does two things for us: it returns a
low-level file handle and a random file name, the latter we use as
database name.  We just have to keep the `db_fd` around so that we can use
the :func:`os.close` function to close the file.

If we now run that test suite, we should see the following output::

    $ python flaskr_tests.py

    ----------------------------------------------------------------------
    Ran 0 tests in 0.000s

    OK

Even though it did not run any tests, we already know that our flaskr
application is syntactically valid, otherwise the import would have died
with an exception.

The First Test
--------------

Now we can add the first test.  Let's check that the application shows
"No entries here so far" if we access the root of the application (``/``).
For that we modify our created test case class so that it looks like
this::

    class FlaskrTestCase(unittest.TestCase):

        def setUp(self):
            self.db_fd, flaskr.app.config['DATABASE'] = tempfile.mkstemp()
            self.app = flaskr.app.test_client()
            flaskr.init_db()

        def tearDown(self):
            os.close(self.db_fd)
            os.unlink(flaskr.DATABASE)

        def test_empty_db(self):
            rv = self.app.get('/')
            assert 'No entries here so far' in rv.data

Test functions begin with the word `test`.  Every function named like that
will be picked up automatically.  By using `self.app.get` we can send an
HTTP `GET` request to the application with the given path.  The return
value will be a :class:`~flask.Flask.response_class` object.  We can now
use the :attr:`~werkzeug.BaseResponse.data` attribute to inspect the
return value (as string) from the application.  In this case, we ensure
that ``'No entries here so far'`` is part of the output.

Run it again and you should see one passing test::

    $ python flaskr_tests.py
    .
    ----------------------------------------------------------------------
    Ran 1 test in 0.034s

    OK

Of course you can submit forms with the test client as well, which we will
use now to log our user in.

Logging In and Out
------------------

The majority of the functionality of our application is only available for
the administrative user, so we need a way to log our test client in to the
application and out of it again.  For that we fire some requests to the
login and logout pages with the required form data (username and
password).  Because the login and logout pages redirect, we tell the
client to `follow_redirects`.

Add the following two methods to your `FlaskrTestCase` class::

   def login(self, username, password):
       return self.app.post('/login', data=dict(
           username=username,
           password=password
       ), follow_redirects=True)

   def logout(self):
       return self.app.get('/logout', follow_redirects=True)

Now we can easily test if logging in and out works and that it fails with
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

Now we can also test that adding messages works.  Add a new test method
like this::

    def test_messages(self):
        self.login('admin', 'default')
        rv = self.app.post('/add', data=dict(
            title='<Hello>',
            text='<strong>HTML</strong> allowed here'
        ), follow_redirects=True)
        assert 'No entries here so far' not in rv.data
        assert '&lt;Hello&gt' in rv.data
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
`MiniTwit Example`_ from the sources.  That one contains a larger test
suite.


.. _MiniTwit Example:
   http://github.com/mitsuhiko/flask/tree/master/examples/minitwit/


Other Testing Tricks
--------------------

Besides using the test client we used above, there is also the
:meth:`~flask.Flask.test_request_context` method that in combination with
the `with` statement can be used to activate a request context
temporarily.  With that you can access the :class:`~flask.request`,
:class:`~flask.g` and :class:`~flask.session` objects like in view
functions.  Here's a full example that showcases this::

    app = flask.Flask(__name__)

    with app.test_request_context('/?name=Peter'):
        assert flask.request.path == '/'
        assert flask.request.args['name'] == 'Peter'

All the other objects that are context bound can be used the same.

If you want to test your application with different configurations and
there does not seem to be a good way to do that, consider switching to
application factories (see :ref:`app-factories`).


Keeping the Context Around
--------------------------

.. versionadded:: 0.4

Sometimes it can be helpful to trigger a regular request but keep the
context around for a little longer so that additional introspection can
happen.  With Flask 0.4 this is possible by using the
:meth:`~flask.Flask.test_client` with a `with` block::

    app = flask.Flask(__name__)

    with app.test_client() as c:
        rv = c.get('/?tequila=42')
        assert request.args['tequila'] == '42'

If you would just be using the :meth:`~flask.Flask.test_client` without
the `with` block, the `assert` would fail with an error because `request`
is no longer available (because used outside of an actual request).
Keep in mind however that :meth:`~flask.Flask.after_request` functions
are already called at that point so your database connection and
everything involved is probably already closed down.
