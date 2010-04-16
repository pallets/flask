.. _testing:

Testing Flask Applications
==========================

   **Something that is untested is broken.**

Not sure where that is coming from, and it's not entirely correct, but
also not that far from the truth.  Untested applications make it hard to
improve existing code and developers of untested applications tend to
become pretty paranoid.  If an application however has automated tests you
can savely change things and you will instantly know if your change broke
something.

Flask gives you a couple of ways to test applications.  It mainly does
that by exposing the Werkzeug test :class:`~werkzeug.Client` class to your
code and handling the context locals for you.  You can then use that with
your favourite testing solution.  In this documentation we will us the
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

    import unittest
    import flaskr
    import tempfile

    class FlaskrTestCase(unittest.TestCase):

        def setUp(self):
            self.db = tempfile.NamedTemporaryFile()
            self.app = flaskr.app.test_client()
            flaskr.DATABASE = self.db.name
            flaskr.init_db()

    if __name__ == '__main__':
        unittest.main()

The code in the `setUp` function creates a new test client and initialize
a new database.  That function is called before each individual test function.
What the test client does for us is giving us a simple interface to the
application.  We can trigger test requests to the application and the
client will also keep track of cookies for us.

Because SQLite3 is filesystem based we can easily use the tempfile module
to create a temporary database and initialize it.  Just make sure that you
keep a reference to the :class:`~tempfile.NamedTemporaryFile` around (we
store it as `self.db` because of that) so that the garbage collector does
not remove that object and with it the database from the filesystem.

If we now run that testsuite, we should see the following output::

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
            self.db = tempfile.NamedTemporaryFile()
            self.app = flaskr.app.test_client()
            flaskr.DATABASE = self.db.name
            flaskr.init_db()

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

Of course you can submit forms with the test client as well which we will
use now to log our user in.

Logging In and Out
------------------

The majority of the functionality of our application is only available for
the administration user.  So we need a way to log our test client into the
application and out of it again.  For that we fire some requests to the
login and logout pages with the required form data (username and
password).  Because the login and logout pages redirect, we tell the
client to `follow_redirects`.

Add the following two methods do your `FlaskrTestCase` class::

   def login(self, username, password):
       return self.app.post('/login', data=dict(
           username=username,
           password=password
       ), follow_redirects=True)

   def logout(self):
       return self.app.get('/logout', follow_redirects=True)

Now we can easily test if logging in and out works and that it fails with
invalid credentials.  Add this as new test to the class::

   def test_login_logout(self):
       rv = self.login(flaskr.USERNAME, flaskr.PASSWORD)
       assert 'You were logged in' in rv.data
       rv = self.logout()
       assert 'You were logged out' in rv.data
       rv = self.login(flaskr.USERNAME + 'x', flaskr.PASSWORD)
       assert 'Invalid username' in rv.data
       rv = self.login(flaskr.USERNAME, flaskr.PASSWORD + 'x')
       assert 'Invalid password' in rv.data

Test Adding Messages
--------------------

Now we can also test that adding messages works.  Add a new test method
like this::

    def test_messages(self):
        self.login(flaskr.USERNAME, flaskr.PASSWORD)
        rv = self.app.post('/add', data=dict(
            title='<Hello>',
            text='<strong>HTML</strong> allowed here'
        ), follow_redirects=True)
        assert 'No entries here so far' not in rv.data
        self.login(flaskr.USERNAME, flaskr.PASSWORD)
        assert '&lt;Hello&gt' in rv.data
        assert '<strong>HTML</strong> allowed here' in rv.data

Here we also check that HTML is allowed in the text but not in the title
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
