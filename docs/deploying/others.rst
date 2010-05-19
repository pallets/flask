Other Servers
=============

There are popular servers written in Python that allow the execution of
WSGI applications as well.  Keep in mind though that some of these servers
were written for very specific applications and might not work as well for
standard WSGI application such as Flask powered ones.


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

.. _Gunicorn: http://gunicorn.org/
.. _eventlet: http://eventlet.net/
.. _greenlet: http://codespeak.net/py/0.9.2/greenlet.html

