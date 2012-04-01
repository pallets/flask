.. _deploying-other-servers:

Other Servers
=============

There are popular servers written in Python that allow the execution of WSGI
applications as well.  These servers stand alone when they run; you can proxy
to them from your web server.

Tornado
--------

`Tornado`_ is an open source version of the scalable, non-blocking web
server and tools that power `FriendFeed`_.  Because it is non-blocking and
uses epoll, it can handle thousands of simultaneous standing connections,
which means it is ideal for real-time web services.  Integrating this
service with Flask is a trivial task::

    from tornado.wsgi import WSGIContainer
    from tornado.httpserver import HTTPServer
    from tornado.ioloop import IOLoop
    from yourapplication import app

    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(5000)
    IOLoop.instance().start()


.. _Tornado: http://www.tornadoweb.org/
.. _FriendFeed: http://friendfeed.com/

Gevent
-------

`Gevent`_ is a coroutine-based Python networking library that uses
`greenlet`_ to provide a high-level synchronous API on top of `libevent`_
event loop::

    from gevent.wsgi import WSGIServer
    from yourapplication import app

    http_server = WSGIServer(('', 5000), app)
    http_server.serve_forever()

.. _Gevent: http://www.gevent.org/
.. _greenlet: http://codespeak.net/py/0.9.2/greenlet.html
.. _libevent: http://monkey.org/~provos/libevent/

Gunicorn
--------

`Gunicorn`_ 'Green Unicorn' is a WSGI HTTP Server for UNIX. It's a pre-fork
worker model ported from Ruby's Unicorn project. It supports both `eventlet`_
and `greenlet`_. Running a Flask application on this server is quite simple::

    gunicorn myproject:app

`Gunicorn`_ provides many command-line options -- see ``gunicorn -h``.
For example, to run a Flask application with 4 worker processes (``-w
4``) binding to localhost port 4000 (``-b 127.0.0.1:4000``)::

    gunicorn -w 4 -b 127.0.0.1:4000 myproject:app

.. _Gunicorn: http://gunicorn.org/
.. _eventlet: http://eventlet.net/
.. _greenlet: http://codespeak.net/py/0.9.2/greenlet.html

Proxy Setups
------------

If you deploy your application using one of these servers behind an HTTP
proxy you will need to rewrite a few headers in order for the
application to work.  The two problematic values in the WSGI environment
usually are `REMOTE_ADDR` and `HTTP_HOST`.  Werkzeug ships a fixer that
will solve some common setups, but you might want to write your own WSGI
middleware for specific setups.

The most common setup invokes the host being set from `X-Forwarded-Host`
and the remote address from `X-Forwarded-For`::

    from werkzeug.contrib.fixers import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app)

Please keep in mind that it is a security issue to use such a middleware
in a non-proxy setup because it will blindly trust the incoming
headers which might be forged by malicious clients.

If you want to rewrite the headers from another header, you might want to
use a fixer like this::

    class CustomProxyFix(object):

        def __init__(self, app):
            self.app = app

        def __call__(self, environ, start_response):
            host = environ.get('HTTP_X_FHOST', '')
            if host:
                environ['HTTP_HOST'] = host
            return self.app(environ, start_response)

    app.wsgi_app = CustomProxyFix(app.wsgi_app)
