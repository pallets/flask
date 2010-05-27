CGI
===

If all other deployment methods do not work, CGI will work for sure.  CGI
is supported by all major servers but usually has a less-than-optimal
performance.

This is also the way you can use a Flask application on Google's
`App Engine`_, there however the execution does happen in a CGI-like
environment.  The application's performance is unaffected because of that.

.. admonition:: Watch Out

   Please make sure in advance that your ``app.run()`` call you might
   have in your application file, is inside an ``if __name__ ==
   '__main__':`` or moved to a separate file.  Just make sure it's not
   called because this will always start a local WSGI server which we do
   not want if we deploy that application to CGI / app engine.

.. _App Engine: http://code.google.com/appengine/

Creating a `.cgi` file
----------------------

First you need to create the CGI application file.  Let's call it
`yourapplication.cgi`::

    #!/usr/bin/python
    from wsgiref.handlers import CGIHandler
    from yourapplication import app

    CGIHandler().run(app)

If you're running Python 2.4 you will need the :mod:`wsgiref` package.  Python
2.5 and higher ship this as part of the standard library.

Server Setup
------------

Usually there are two ways to configure the server.  Either just copy the
`.cgi` into a `cgi-bin` (and use `mod_rerwite` or something similar to
rewrite the URL) or let the server point to the file directly.

In Apache for example you can put a like like this into the config:

.. sourcecode:: apache

    ScriptAlias /app /path/to/the/application.cgi

For more information consult the documentation of your webserver.
