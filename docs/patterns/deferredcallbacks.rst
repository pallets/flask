.. _deferred-callbacks:

Deferred Request Callbacks
==========================

One of the design principles of Flask is that response objects are created
and passed down a chain of potential callbacks that can modify them or
replace them.  When the request handling starts, there is no response
object yet.  It is created as necessary either by a view function or by
some other component in the system.

But what happens if you want to modify the response at a point where the
response does not exist yet?  A common example for that would be a
before-request function that wants to set a cookie on the response object.

One way is to avoid the situation.  Very often that is possible.  For
instance you can try to move that logic into an after-request callback
instead.  Sometimes however moving that code there is just not a very
pleasant experience or makes code look very awkward.

As an alternative possibility you can attach a bunch of callback functions
to the :data:`~flask.g` object and call them at the end of the request.
This way you can defer code execution from anywhere in the application.


The Decorator
-------------

The following decorator is the key.  It registers a function on a list on
the :data:`~flask.g` object::

    from flask import g

    def after_this_request(f):
        if not hasattr(g, 'after_request_callbacks'):
            g.after_request_callbacks = []
        g.after_request_callbacks.append(f)
        return f


Calling the Deferred
--------------------

Now you can use the `after_this_request` decorator to mark a function to
be called at the end of the request.  But we still need to call them.  For
this the following function needs to be registered as
:meth:`~flask.Flask.after_request` callback::

    @app.after_request
    def call_after_request_callbacks(response):
        for callback in getattr(g, 'after_request_callbacks', ()):
            callback(response)
        return response


A Practical Example
-------------------

At any time during a request, we can register a function to be called at the
end of the request.  For example you can remember the current language of the
user in a cookie in the before-request function::

    from flask import request

    @app.before_request
    def detect_user_language():
        language = request.cookies.get('user_lang')
        if language is None:
            language = guess_language_from_request()
            @after_this_request
            def remember_language(response):
                response.set_cookie('user_lang', language)
        g.language = language
