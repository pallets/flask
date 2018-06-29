Dreamhost Setup
===============

These instructions are specifically for deploying to Dreamhost.

1. Add hosting to a new domain in the ``Manage Domains`` tab of your
   control panel.

2. During setup, click the ``Passenger (Ruby/NodeJS/Python apps only):``
   checkbox to enable Phusion Passenger on your domain.

3. Set up the user as a shell user in the ``Users > Manage Users`` tab
   in the control panel. Dreamhost users default to SFTP only.

4. SSH into your new server. Clone the repository into your site’s
   directory. It will look like
   ``/home/dh_username/something.domain.com``.

::

    cd /home/dh_username/something.domain.com
    git clone https://github.com/username/project-name.git project-name

5. `Install a custom version of Python
   3. <https://help.dreamhost.com/hc/en-us/articles/115000702772-Installing-a-custom-version-of-Python-3>`__

6. `Set up a new
   virtualenv <https://help.dreamhost.com/hc/en-us/articles/115000695551-Installing-and-using-virtualenv-with-Python-3>`__
   in a separate directory inside
   ``/home/dh_username/something.domain.com/project-name/venv``.

7. With your virtualenv activated (refer to step 4 for help), install
   `Flask <http://flask.pocoo.org/>`__ with ``pip3 install Flask``

8. You’ll want to create a ``passenger_wsgi.py`` file in
   ``/home/dh_username/something.domain.com/`` with these contents,
   modified for your username, project name, or any other directory
   differences you have.

::

    import sys, os
    #
    INTERP = "/home/dh_username/something.domain.com/project-name/venv/bin/python3"
    #INTERP is present twice so that the new Python interpreter knows the actual executable path
    if sys.executable != INTERP: os.execl(INTERP, INTERP, *sys.argv)
    sys.path.append(os.getcwd())

    sys.path.append('project-name')
    import project-name

    application = project-name.create_app()

This assumes that when you clone your project, the \_\ *init\_*.py file
is in the project-name directory, since you’ll need to import it as a
module.

9. In your site’s root directory, do the following

::

    mkdir tmp
    touch tmp/restart.txt

Every time you make changes to your Passenger app, touch
``tmp/restart.txt``\ to restart.
