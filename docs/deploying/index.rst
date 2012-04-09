.. _deployment:

Deployment Options
==================

Depending on what you have available there are multiple ways to run
Flask applications.  You can use the builtin server during development,
but you should use a full deployment option for production applications.
(Do not use the builtin development server in production.)  Several
options are available and documented here.

If you have a different WSGI server look up the server documentation
about how to use a WSGI app with it.  Just remember that your
:class:`Flask` application object is the actual WSGI application.

For hosted options to get up and running quickly, see
:ref:`quickstart_deployment` in the Quickstart.

.. toctree::
   :maxdepth: 2

   mod_wsgi
   wsgi-standalone
   uwsgi
   fastcgi
   cgi
