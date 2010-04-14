Deployment Options
==================

Depending on what you have available there are multiple ways to run Flask
applications.  A very common method is to use the builtin server during
development and maybe behind a proxy for simple applications, but there
are more options available.

If you have a different WSGI server look up the server documentation about
how to use a WSGI app with it.  Just remember that your application object
is the actual WSGI application.


FastCGI
-------

A very popular deployment setup on servers like `lighttpd`_ and `nginx`_
is FastCGI.  To use your WSGI application with any of them you will need
a FastCGI server first.

The most popular one is `flup`_ which we will use for this guide.  Make
sure to have it installed.

Creating a `.fcgi` file
```````````````````````

First you need to create the FastCGI server file.  Let's call it
`yourapplication.fcgi`::

    #!/usr/bin/python
    from flup.server.fcgi import WSGIServer
    from yourapplication import app

    WSGIServer(app).run()

This is enough for Apache to work, however lighttpd and nginx need a
socket to communicate with the FastCGI server.  For that to work you
need to pass the path to the socket to the
:class:`~flup.server.fcgi.WSGIServer`::

    WSGIServer(application, bindAddress='/path/to/fcgi.sock').run()

The path has to be the exact same path you define in the server
config.

Save the `yourapplication.fcgi` file somewhere you will find it again.
It makes sense to have that in `/var/www/yourapplication` or something
similar.

Make sure to set the executable bit on that file so that the servers
can execute it::

    # chmod +x /var/www/yourapplication/yourapplication.fcgi

Configuring lighttpd
````````````````````

A basic FastCGI configuration for lighttpd looks like that::

    fastcgi.server = ("/yourapplication" =>
        "yourapplication" => (
            "socket" => "/tmp/yourapplication-fcgi.sock",
            "bin-path" => "/var/www/yourapplication/yourapplication.fcgi",
            "check-local" => "disable"
        )
    )

This configuration binds the application to `/yourapplication`.  If you
want the application to work in the URL root you have to work around a
lighttpd bug with the :class:`~werkzeug.contrib.fixers.LighttpdCGIRootFix`
middleware.

Make sure to apply it only if you are mounting the application the URL
root.

Configuring nginx
`````````````````

Installing FastCGI applications on nginx is a bit tricky because by default
some FastCGI parameters are not properly forwarded.

A basic FastCGI configuration for nginx looks like this::

    location /yourapplication/ {
        include fastcgi_params;
        if ($uri ~ ^/yourapplication/(.*)?) {
            set $path_url $1;
        }
        fastcgi_param PATH_INFO $path_url;
        fastcgi_param SCRIPT_NAME /yourapplication;
        fastcgi_pass unix:/tmp/yourapplication-fcgi.sock;
    }

This configuration binds the application to `/yourapplication`.  If you want
to have it in the URL root it's a bit easier because you don't have to figure
out how to calculate `PATH_INFO` and `SCRIPT_NAME`::

    location /yourapplication/ {
        include fastcgi_params;
        fastcgi_param PATH_INFO $fastcgi_script_name;
        fastcgi_param SCRIPT_NAME "";
        fastcgi_pass unix:/tmp/yourapplication-fcgi.sock;
    }

Since Nginx doesn't load FastCGI apps, you have to do it by yourself.  You
can either write an `init.d` script for that or execute it inside a screen
session::

    $ screen
    $ /var/www/yourapplication/yourapplication.fcgi

Debugging
`````````

FastCGI deployments tend to be hard to debug on most webservers.  Very often the
only thing the server log tells you is something along the lines of "premature
end of headers".  In order to debug the application the only thing that can
really give you ideas why it breaks is switching to the correct user and
executing the application by hand.

This example assumes your application is called `application.fcgi` and that your
webserver user is `www-data`::

    $ su www-data
    $ cd /var/www/yourapplication
    $ python application.fcgi
    Traceback (most recent call last):
      File "yourapplication.fcg", line 4, in <module>
    ImportError: No module named yourapplication

In this case the error seems to be "yourapplication" not being on the python
path.  Common problems are:

-   relative paths being used.  Don't rely on the current working directory
-   the code depending on environment variables that are not set by the
    web server.
-   different python interpreters being used.

.. _lighttpd: http://www.lighttpd.net/
.. _nginx: http://nginx.net/
.. _flup: http://trac.saddi.com/flup


mod_wsgi (Apache)
-----------------

If you are using the `Apache`_ webserver you should consider using `mod_wsgi`_.

.. _Apache: http://httpd.apache.org/

Installing `mod_wsgi`
`````````````````````

If you don't have `mod_wsgi` installed yet you have to either install it using
a package manager or compile it yourself.

The mod_wsgi `installation instructions`_ cover installation instructions for
source installations on UNIX systems.

If you are using ubuntu / debian you can apt-get it and activate it as follows::

    # apt-get install libapache2-mod-wsgi

On FreeBSD install `mod_wsgi` by compiling the `www/mod_wsgi` port or by using
pkg_add::

    # pkg_add -r mod_wsgi

If you are using pkgsrc you can install `mod_wsgi` by compiling the
`www/ap2-wsgi` package.

If you encounter segfaulting child processes after the first apache reload you
can safely ignore them.  Just restart the server.

Creating a `.wsgi` file
```````````````````````

To run your application you need a `yourapplication.wsgi` file.  This file
contains the code `mod_wsgi` is executing on startup to get the application
object.  The object called `application` in that file is then used as
application.

For most applications the following file should be sufficient::

    from yourapplication import app as application

If you don't have a factory function for application creation but a singleton
instance you can directly import that one as `application`.

Store that file somewhere where you will find it again (eg:
`/var/www/yourapplication`) and make sure that `yourapplication` and all
the libraries that are in use are on the python load path.  If you don't
want to install it system wide consider using a `virtual python`_ instance.

Configuring Apache
``````````````````

The last thing you have to do is to create an Apache configuration file for
your application.  In this example we are telling `mod_wsgi` to execute the
application under a different user for security reasons:

.. sourcecode:: apache

    <VirtualHost *>
        ServerName example.com

        WSGIDaemonProcess yourapplication user=user1 group=group1 threads=5
        WSGIScriptAlias / /var/www/yourapplication/yourapplication.wsgi

        <Directory /var/www/yourapplication>
            WSGIProcessGroup yourapplication
            WSGIApplicationGroup %{GLOBAL}
            Order deny,allow
            Allow from all
        </Directory>
    </VirtualHost>

For more information consult the `mod_wsgi wiki`_.

.. _mod_wsgi: http://code.google.com/p/modwsgi/
.. _installation instructions: http://code.google.com/p/modwsgi/wiki/QuickInstallationGuide
.. _virtual python: http://pypi.python.org/pypi/virtualenv
.. _mod_wsgi wiki: http://code.google.com/p/modwsgi/wiki/



Tornado
--------

`Tornado`_ is an open source version of the scalable, non-blocking web server and tools that power `FriendFeed`_.
Because it is non-blocking and uses epoll, it can handle thousands of simultaneous standing connections, which means it is ideal for real-time web services.
Integrating this service with Flask is a trivial task::

    
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

`Gevent`_ is a coroutine-based Python networking library that uses `greenlet`_ to provide a high-level synchronous API on top of `libevent`_ event loop::

    from gevent.wsgi import WSGIServer
    from yourapplication import app

    http_server = WSGIServer(('', 5000), app)
    http_server.serve_forever()

.. _Gevent: http://www.gevent.org/
.. _greenlet: http://codespeak.net/py/0.9.2/greenlet.html
.. _libevent: http://monkey.org/~provos/libevent/

CGI
---

If all other deployment methods do not work, CGI will work for sure.  CGI
is supported by all major browsers but usually has a less-than-optimal
performance.

This is also the way you can use a Flask application on Google's
`AppEngine`_, there however the execution does happen in a CGI-like
environment.  The application's performance is unaffected because of that.

.. _AppEngine: http://code.google.com/appengine/

Creating a `.cgi` file
``````````````````````

First you need to create the CGI application file.  Let's call it
`yourapplication.cgi`::

    #!/usr/bin/python
    from wsgiref.handlers import CGIHandler
    from yourapplication import app

    CGIHandler().run(app)

If you're running Python 2.4 you will need the :mod:`wsgiref` package.  Python
2.5 and higher ship this as part of the standard library.

Server Setup
````````````

Usually there are two ways to configure the server.  Either just copy the
`.cgi` into a `cgi-bin` (and use `mod_rerwite` or something similar to
rewrite the URL) or let the server point to the file directly.

In Apache for example you can put a like like this into the config:

.. sourcecode:: apache

    ScriptName /app /path/to/the/application.cgi

For more information consult the documentation of your webserver.

