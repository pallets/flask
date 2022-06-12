Deploying to Production
=======================

After developing your application, you'll want to make it available
publicly to other users. When you're developing locally, you're probably
using the built-in development server, debugger, and reloader. These
should not be used in production. Instead, you should use a dedicated
WSGI server or hosting platform, some of which will be described here.

"Production" means "not development", which applies whether you're
serving your application publicly to millions of users or privately /
locally to a single user. **Do not use the development server when
deploying to production. It is intended for use only during local
development. It is not designed to be particularly secure, stable, or
efficient.**

Self-Hosted Options
-------------------

Flask is a WSGI *application*. A WSGI *server* is used to run the
application, converting incoming HTTP requests to the standard WSGI
environ, and converting outgoing WSGI responses to HTTP responses.

The primary goal of these docs is to familiarize you with the concepts
involved in running a WSGI application using a production WSGI server
and HTTP server. There are many WSGI servers and HTTP servers, with many
configuration possibilities. The pages below discuss the most common
servers, and show the basics of running each one. The next section
discusses platforms that can manage this for you.

.. toctree::
    :maxdepth: 1

    gunicorn
    waitress
    mod_wsgi
    uwsgi
    gevent
    eventlet
    asgi

WSGI servers have HTTP servers built-in. However, a dedicated HTTP
server may be safer, more efficient, or more capable. Putting an HTTP
server in front of the WSGI server is called a "reverse proxy."

.. toctree::
    :maxdepth: 1

    proxy_fix
    nginx
    apache-httpd

This list is not exhaustive, and you should evaluate these and other
servers based on your application's needs. Different servers will have
different capabilities, configuration, and support.


Hosting Platforms
-----------------

There are many services available for hosting web applications without
needing to maintain your own server, networking, domain, etc. Some
services may have a free tier up to a certain time or bandwidth. Many of
these services use one of the WSGI servers described above, or a similar
interface. The links below are for some of the most common platforms,
which have instructions for Flask, WSGI, or Python.

- `PythonAnywhere <https://help.pythonanywhere.com/pages/Flask/>`_
- `Heroku <https://devcenter.heroku.com/articles/getting-started-with-python>`_
- `Google App Engine <https://cloud.google.com/appengine/docs/standard/python3/building-app>`_
- `Google Cloud Run <https://cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-service>`_
- `AWS Elastic Beanstalk <https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-flask.html>`_
- `Microsoft Azure <https://docs.microsoft.com/en-us/azure/app-service/quickstart-python>`_

This list is not exhaustive, and you should evaluate these and other
services based on your application's needs. Different services will have
different capabilities, configuration, pricing, and support.

You'll probably need to :doc:`proxy_fix` when using most hosting
platforms.
