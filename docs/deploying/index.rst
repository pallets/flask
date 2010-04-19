Deployment Options
==================

Depending on what you have available there are multiple ways to run Flask
applications.  A very common method is to use the builtin server during
development and maybe behind a proxy for simple applications, but there
are more options available.

If you have a different WSGI server look up the server documentation about
how to use a WSGI app with it.  Just remember that your application object
is the actual WSGI application.

.. toctree::
   :maxdepth: 2

   mod_wsgi
   cgi
   fastcgi
   others
