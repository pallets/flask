.. _deployment:

Deployment Options
==================

While lightweight and easy to use, **Flask's built-in server is not suitable
for production** as it doesn't scale well and by default serves only one
request at a time.  Some of the options available for properly running Flask in
production are documented here.

If you want to deploy your Flask application to a WSGI server not listed here,
look up the server documentation about how to use a WSGI app with it.  Just
remember that your :class:`Flask` application object is the actual WSGI
application.


Hosted options
--------------

- `Deploying Flask on Heroku <https://devcenter.heroku.com/articles/getting-started-with-python>`_
- `Deploying Flask on OpenShift <https://developers.openshift.com/en/python-flask.html>`_
- `Deploying Flask on Webfaction <http://flask.pocoo.org/snippets/65/>`_
- `Deploying Flask on Google App Engine <https://github.com/kamalgill/flask-appengine-template>`_
- `Deploying Flask on AWS Elastic Beanstalk <http://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-flask.html>`_
- `Sharing your Localhost Server with Localtunnel <http://flask.pocoo.org/snippets/89/>`_
- `Deploying on Azure (IIS) <https://azure.microsoft.com/documentation/articles/web-sites-python-configure/>`_
- `Deploying on PythonAnywhere <https://help.pythonanywhere.com/pages/Flask/>`_

Self-hosted options
-------------------

.. toctree::
   :maxdepth: 2

   mod_wsgi
   wsgi-standalone
   uwsgi
   fastcgi
   cgi
