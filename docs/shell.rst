Working with the Shell
======================

One of the reasons everybody loves Python is the interactive shell. It allows
you to play around with code in real time and immediately get results back.
Flask provides the ``flask shell`` CLI command to start an interactive Python
shell with some setup done to make working with the Flask app easier.

.. code-block:: text

    $ flask shell

Creating a Request Context
--------------------------

``flask shell`` pushes an app context automatically, so :data:`.current_app` and
:data:`.g` are already available. However, there is no HTTP request being
handled in the shell, so :data:`.request` and :data:`.session` are not yet
available.

The easiest way to create a proper request context from the shell is by
using the :attr:`~flask.Flask.test_request_context` method which creates
us a :class:`~flask.ctx.RequestContext`:

>>> ctx = app.test_request_context()

Normally you would use the ``with`` statement to make this context active, but
in the shell it's easier to call :meth:`~.RequestContext.push` and
:meth:`~.RequestContext.pop` manually:

>>> ctx.push()

From that point onwards you can work with the request object until you call
``pop``:

>>> ctx.pop()

Firing Before/After Request
---------------------------

By just creating a request context, you still don't have run the code that
is normally run before a request.  This might result in your database
being unavailable if you are connecting to the database in a
before-request callback or the current user not being stored on the
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

The functions registered as :meth:`~flask.Flask.teardown_request` are
automatically called when the context is popped.  So this is the perfect
place to automatically tear down resources that were needed by the request
context (such as database connections).


Further Improving the Shell Experience
--------------------------------------

If you like the idea of experimenting in a shell, create yourself a module
with stuff you want to star import into your interactive session.  There
you could also define some more helper methods for common things such as
initializing the database, dropping tables etc.

Just put them into a module (like `shelltools`) and import from there:

>>> from shelltools import *
