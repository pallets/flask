Heroku Deployment
=================

During and after developing your application, you'll want to make it available
publicly to other users. When you're developing locally, you're using the 
built-in development server, debugger, and reloader. These should not be 
used in production. InsteadHeroku Deployment

During and after developing your application, you'll want to make it available
publicly to other users. When you're developing locally, you're using the 
built-in development server, debugger, and reloader. These should not be 
used in production. Instead, you should use a dedicated server hosting platform 
such as Heroku. The process of successfully hosting your application on Heroku 
will be outlined here.

As of November 28, 2022, Heroku has discontinued their free dyno management services 
for developers to host their projects. Dynos are containers provided by Heroku that
holds deployed applications. Under specific criteria, Users are allocated a finite  
amount of free dyno hours for their deployed projects every month. This tutorial 
utilizes `Gunicorn`_, a Python WSGI HTTP Server where Heroku requires dyno hours. Please 
refer to `Heroku's Free Dyno Hours`_ for more information regarding Heroku's free dyno
hours. 

.. _Gunicorn: https://gunicorn.org/
.. _Heroku's Free Dyno Hours: https://devcenter.heroku.com/articles/free-dyno-hours/


Requirements
-------------

Heroku requires the application to define a set of processes before
running the environment. Because Flask is a WSGI *application*,
to deploy it, your application will require WSGI *server*. The 
Gunicorn  pure WSGI server is utilized as the
server for Flask applications. For a Gunicorn installation guide
visit :doc:`<../gunicorn.rst>`. This will generate ``Procfile`` in your
application's root directory
.
.. code-block:: text

    web: gunicorn app:app

This communicates to run ``app.py`` and to set the ``app`` name to be ``app``.

Your application now requires a ``requirements.txt`` in the root directory. This
document communicates the libraries that the application utilizes to the Heroku.
This is similar to installing libraries and on your local directories.

To create this document, run the following in the root directory:

.. code-block:: text

    pip freeze > requirements.txt

The root directory of your Flask application should contain a ``requirements.txt``
that contains a list of the version of libraries used.

.. code-block:: text

    certifi==2020.12.5
    chardet==4.0.0
    click==7.1.2
    Flask==1.1.2
    gunicorn==20.1.0
    Jinja2==2.11.3
    MarkupSafe==1.1.1
    requests==2.25.1

A registered account on Heroku and Github is required. Create a repository and push
your application into the Github repository if not already done.


Deployment
----------

Log into your Heroku account and locate and select the ``New`` button and select
``Create new app``. Follow the instructions to create your new app on Heroku. When
the application is created, you'll be presented with your Heroku App home page.
Locate the ``Deployment method`` and chose the option to connect to Github. You'll
be prompted to your Github account to authorize the connection to Heroku. Now you'll
see the ``Connect to GitHub`` row. Select  and connect the repository your Flask 
application is located in.

You have the choice to enable automatic deployment or to manually deploy your 
application. Automatic deployment will deploy the new version of your Heroku app
with every branch push the Github repository. To enable, click the ``Enable Automatic Deploys``
button. On the other hand, if you prefer manual deployment, select your branch and
click the ``Deploy Branch``.

Your application will be built and if successful it will be deployed on Heroku.
Click the ``View`` button to access your newly deployed Flask application.
, you should use a dedicated server hosting platform 
such as Heroku. The process of successfully hosting your application on Heroku 
will be outlined here.