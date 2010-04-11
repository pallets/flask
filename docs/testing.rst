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

First we need an application to test for functionality.  Let's start
simple with a Hello World application (`hello.py`)::

    from flask import Flask, render_template_string
    app = Flask(__name__)

    @app.route('/')
    @app.route('/<name>')
    def hello(name='World'):
        return render_template_string('''
            <!doctype html>
            <title>Hello {{ name }}!</title>
            <h1>Hello {{ name }}!</h1>
        ''', name=name)

The Testing Skeleton
--------------------

In order to test that, we add a second module (
`hello_tests.py`) and create a unittest skeleton there::

    import unittest
    import hello

    class HelloWorldTestCase(unittest.TestCase):

        def setUp(self):
            self.app = hello.app.test_client()

    if __name__ == '__main__':
        unittest.main()

The code in the `setUp` function creates a new test client.  That function
is called before each individual test function.  What the test client does
for us is giving us a simple interface to the application.  We can trigger
test requests to the application and the client will also keep track of
cookies for us.

If we now run that testsuite, we should see the following output::

    $ python hello_tests.py

    ----------------------------------------------------------------------
    Ran 0 tests in 0.000s
    
    OK

Even though it did not run any tests, we already know that our hello
application is syntactically valid, otherwise the import would have died
with an exception.

The First Test
--------------

Now we can add the first test.  Let's check that the application greets us
with "Hello World" if we access it on ``/``.  For that we modify our
created test case class so that it looks like this::

    class HelloWorldTestCase(unittest.TestCase):

        def setUp(self):
            self.app = hello.app.test_client()

        def test_hello_world(self):
            rv = self.app.get('/')
            assert 'Hello World!' in rv.data

Test functions begin with the word `test`.  Every function named like that
will be picked up automatically.  By using `self.app.get` we can send an
HTTP `GET` request to the application with the given path.  The return
value will be a :class:`~flask.Flask.response_class` object.  We can now
use the :attr:`~werkzeug.BaseResponse.data` attribute to inspect the
return value (as string) from the application.  In this case, we ensure
that ``'Hello World!'`` is part of the output.

Run it again and you should see one passing test.  Let's add a second test
here::

        def test_hello_name(self):
            rv = self.app.get('/Peter')
            assert 'Hello Peter!' in rv.data

Of course you can submit forms with the test client as well.  For that and
other features of the test client, check the documentation of the Werkzeug
test :class:`~werkzeug.Client` and the tests of the MiniTwit example
application:

-   Werkzeug Test :class:`~werkzeug.Client`
-   `MiniTwit Example`_

.. _MiniTwit Example:
   http://github.com/mitsuhiko/flask/tree/master/examples/minitwit/
