Working with the Shell
======================

.. versionadded:: 0.3

One of the reasons everybody loves Python is the interactive shell.  It
basically allows you to execute Python commands in real time and
immediately get results back.  Flask itself does not come with an
interactive shell, because it does not require any specific setup upfront,
just import your application and start playing around.

There are however some handy helpers to make playing around in the shell a
more pleasant experience.  The main issue with interactive console
sessions is that you're not triggering a request like a browser does which
means that :data:`~flask.g`, :data:`~flask.request` and others are not
available.  But the code you want to test might depend on them, so what
can you do?

This is where some helper functions come in handy.  Keep in mind however
that these functions are not only there for interactive shell usage, but
also for unittesting and other situations that require a faked request
context.

Diving into Context Locals
--------------------------

Say you have a utility function that returns the URL the user should be
redirected to.  Imagine it would always redirect to the URL's ``next``
parameter or the HTTP referrer or the index page::

    from flask import request, url_for

    def redirect_url():
        return request.args.get('next') or \
               request.referrer or \
               url_for('index')

As you can see, it accesses the request object.  If you try to run this
from a plain Python shell, this is the exception you will see:

>>> redirect_url()
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
AttributeError: 'NoneType' object has no attribute 'request'

That makes a lot of sense because we currently do not have a request we
could access.  So we have to make a request and bind it to the current
context.  The :attr:`~flask.Flask.test_request_context` method can create
us a request context:

>>> ctx = app.test_request_context('/?next=http://example.com/')

This context can be used in two ways.  Either with the `with` statement
(which unfortunately is not very handy for shell sessions).  The
alternative way is to call the `push` and `pop` methods:

>>> ctx.push()

From that point onwards you can work with the request object:

>>> redirect_url()
u'http://example.com/'

Until you call `pop`:

>>> ctx.pop()
>>> redirect_url()
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
AttributeError: 'NoneType' object has no attribute 'request'


Firing Before/After Request
---------------------------

By just creating a request context, you still don't have run the code that
is normally run before a request.  This probably results in your database
being unavailable, the current user not being stored on the
:data:`~flask.g` object etc.

This however can easily be done yourself.  Just call
:meth:`~flask.Flask.preprocess_request`:

>>> ctx = app.test_request_context()
>>> ctx.push()
>>> app.preprocess_request()

Keep in mind that the :meth:`~flask.Flask.preprocess_request` function
might return a response object, in that case just ignore it.

To shutdown a request, you need to trick a bit before the after request
functions (triggered by :meth:`~flask.Flask.process_response`) operate on
a response object:

>>> app.process_response(app.response_class())
<Response 0 bytes [200 OK]>
>>> ctx.pop()


Further Improving the Shell Experience
--------------------------------------

If you like the idea of experimenting in a shell, create yourself a module
with stuff you want to star import into your interactive session.  There
you could also define some more helper methods for common things such as
initializing the database, dropping tables etc.

Just put them into a module (like `shelltools` and import from there):

>>> from shelltools import *
