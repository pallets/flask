Quickstart
==========

Eager to get started?  This page gives a good introduction in how to gets
started with Flask.  This assumes you already have Flask installed.  If
you do not, head over to the :ref:`installation` section.


A Minimal Application
---------------------

A minimal Flask application looks something like that::

    from flask import Flask
    app = Flask(__name__)

    @app.route('/')
    def hello_world():
        return "Hello World!"

    if __name__ == '__main__':
        app.run()

If you now start that application with your Python interpreter and head
over to `http://localhost:5000/ <http://localhost:5000/>`_, you should see
your hello world application.

So what did that code do?

1. first we imported the :class:`~flask.Flask` class.  An instance of this
   class will be our WSGI application.
2. next we create an instance of it.  We pass it the name of the module /
   package.  This is needed so that Flask knows where it should look for
   templates, static files and so on.
3. Then we use the :meth:`~flask.Flask.route` decorator to tell Flask
   what URL should trigger our function.
4. The function then has a name which is also used to generate URLs to
   that particular function, and returns the message we want to display in
   the user's browser.
5. Finally we use the :meth:`~flask.Flask.run` function to run the
   local server with our application.  The ``if __name__ == '__main__':``
   makes sure the server only runs if the script is executed directly from
   the Python interpreter and not used as imported module.


Routing
-------

As you have seen above, the :meth:`~flask.Flask.route` decorator is used
to bind a function to a URL.  But there is more to it!  You can make
certain parts of the URL dynamic and attach multiple rules to a function.

Here some examples::

    @app.route('/')
    def index():
        return 'Index Page'

    @app.route('/hello')
    def hello():
        return 'Hello World'


Variable Rules
``````````````

Modern web applications have beautiful URLs.  This helps people remember
the URLs which is especially handy for applications that are used from
mobile devices with slower network connections.  If the user can directly
go to the desired page without having to hit the index page it is more
likely he will like the page and come back next time.

To add variable parts to a URL you can mark these special sections as
``<variable_name>``.  Such a part is then passed as keyword argument to
your function.  Optionally a converter can be specifed by specifying a
rule with ``<converter:variable_name>``.  Here some nice examples::

    @app.route('/user/<username>')
    def show_user_profile(username):
        # show the user profile for that user
        pass

    @app.route('/post/<int:post_id>')
    def show_post(post_id):
        # show the post with the given id, the id is an integer
        pass

The following converters exist:

=========== ===========================================
`int`       accepts integers
`float`     like `int` but for floating point values
`path`      like the default but also accepts slashes
=========== ===========================================


HTTP Methods
````````````

HTTP knows different methods to access URLs.  By default a route only
answers to ``GET`` requests, but that can be changed by providing the
`methods` argument to the :meth:`~flask.Flask.route` decorator.  Here some
examples::

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            do_the_login()
        else:
            show_the_login_form()

If ``GET`` is present, ``HEAD`` will be added automatically for you.  You
don't have to deal with that.  It will also make sure that ``HEAD``
requests are handled like the RFC demands, so you can completely ignore
that part of the HTTP specification.


Accessing Request Data
----------------------

For web applications it's crucial to react to the data a client sent to
the server.  In Flask this information is provided by the global
:class:`~flask.request` object.  If you have some experience with Python
you might be wondering how that object can be global and how Flask
manages to still be threadsafe.  The answer are context locals:

Context Locals
``````````````

.. admonition:: Insider Information

   If you want to understand how that works and how you can implement
   tests with context locals, read this section, otherwise just skip it.

Certain objects in Flask are global objects, but not just a standard
global object, but actually a proxy to an object that is local to a
specific context.  What a mouthful.  But that is actually quite easy to
understand.

Imagine the context being the handling thread.  A request comes in and the
webserver decides to spawn a new thread (or something else, the
underlying object is capable of dealing with other concurrency systems
than threads as well).  When Flask starts its internal request handling it
figures out that the current thread is the active context and binds the
current application and the WSGI environments to that context (thread).
It does that in an intelligent way that one application can invoke another
application without breaking.

So what does this mean to you?  Basically you can completely ignore that
this is the case unless you are unittesting or something different.  You
will notice that code that depends on a request object will suddenly break
because there is no request object.  The solution is creating a request
object yourself and binding it to the context.  The easiest solution for
unittesting is by using the :meth:`~flask.Flask.test_request_context`
context manager.  In combination with the `with` statement it will bind a
test request so that you can interact with it.  Here an example::

    from flask import request

    with app.test_request_context('/hello', method='POST'):
        # now you can do something with the request until the
        # end of the with block, such as basic assertions:
        assert request.path == '/hello'
        assert request.method == 'POST'

The other possibility is passing a whole WSGI environment to the
:meth:`~flask.Flask.request_context` method::

    from flask import request

    with app.request_context(environ):
        assert request.method == 'POST'

The Request Object
``````````````````

The request object is documented in the API section and we will not cover
it here in detail (see :class:`~flask.request`), but just mention some of
the most common operations.  First of all you have to import it from the
the `flask` module::

    from flask import request

The current request method is available by using the
:attr:`~flask.request.method` attribute.  To access form data (data
transmitted in a `POST` or `PUT` request) you can use the
:attr:`~flask.request.form` attribute.  Here a full example of the two
attributes mentioned above::

    @app.route('/login', method=['POST', 'GET'])
    def login():
        error = None
        if request.method == 'POST':
            if valid_login(request.form['username'],
                           request.form['password']):
                return log_the_user_in(request.form['username'])
            else:
                error = 'Invalid username/password'
        # this is executed if the request method was GET or the
        # credentials were invalid

What happens if the key does not exist in the `form` attribute?  In that
case a special :exc:`KeyError` is raised.  You can catch it like a
standard :exc:`KeyError` but if you don't do that, a HTTP 400 Bad Request
error page is shown instead.  So for many situations you don't have to
deal with that problem.

To access parameters submitted in the URL (``?key=value``) you can use the
:attr:`~flask.request.args` attribute::

    searchword = request.args.get('q', '')

We recommend accessing URL parameters with `get` or by catching the
`KeyError` because users might change the URL and presenting them a 400
bad request page in that case is a bit user unfriendly.

For a full list of methods and attribtues on that object, head over to the
:class:`~flask.request` documentation.


File Uploads
````````````

Obviously you can handle uploaded files with Flask just as easy.  Just
make sure not to forget to set the ``enctype="multipart/form-data"``
attribtue on your HTML form, otherwise the browser will not transmit your
files at all.

Uploaded files are stored in memory or at a temporary location on the
filesystem.  You can access those files by looking at the
:attr:`~flask.request.files` attribute on the request object.  Each
uploaded file is stored in that dictionary.  It behaves just like a
standard Python :class:`file` object, but it also has a
:meth:`~werkzeug.FileStorage.save` method that allows you to store that
file on the filesystem of the server.  Here a simple example how that
works::

    from flask import request

    @app.route('/upload', methods=['GET', 'POST'])
    def upload_file():
        if request.method == 'POST':
            f = request.files['the_file']
            f.save('/var/www/uploads/uploaded_file.txt')
        ...

If you want to know how the file was named on the client before it was
uploaded to your application, you can access the
:attr:`~werkzeug.FileStorage.filename` attribute.  However please keep in
mind that this value can be forged so never ever trust that value.  If you
want to use the filename of the client to store the file on the server,
pass it through the :func:`~werkzeug.secure_filename` function that
Werkzeug provides for you::

    from flask import request
    from werkzeug import secure_filename

    @app.route('/upload', methods=['GET', 'POST'])
    def upload_file():
        if request.method == 'POST':
            f= request.files['the_file']
            f.save('/var/www/uploads/' + secure_filename(f.filename))
        ...

Cookies
```````

To access cookies you can use the :attr:`~flask.request.cookies`
attribute.  Again this is a dictionary with all the cookies the client
transmits.  If you want to use sessions, do not use the cookies directly
but instead use the :ref:`sessions` in Flask that add some security on top
of cookies for you.

.. _sessions:

Sessions
--------

Besides the request object there is also a second object called
:class:`~flask.session` that allows you to store information specific to a
user from one request to the next.  This is implemented on top of cookies
for you and signes the cookies cryptographically.  What this means is that
the user could look at the contents of your cookie but not modify it,
unless he knows the secret key used for signing.

In order to use sessions you have to set a secret key.  Here is how
sessions work::

    from flask import session, redirect, url_for, escape

    @app.route('/')
    def index():
        if 'username' in session:
            return 'Logged in as %s' % escape(session['username'])
        return 'You are not logged in'

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            session['username'] = request.form['username']
            return redirect(url_for('index'))
        return '''
            <form action="" method="post">
                <p><input type=text name=username>
                <p><input type=submit value=Login>
            </form>
        '''

    @app.route('/logout')
    def logout():
        # remove the username from the session if its there
        session.pop('username', None)
