.. _installation:

Installation
============

Flask depends on two external libraries, `Werkzeug
<http://werkzeug.pocoo.org/>`_ and `Jinja2 <http://jinja.pocoo.org/2/>`_.
Werkzeug is a toolkit for WSGI, the standard Python interface between web
applications and a variety of servers for both development and deployment.
Jinja2 renders templates.

So how do you get all that on your computer quickly?  There are many ways you
could do that, but the most kick-ass method is virtualenv, so let's have a look
at that first.

You will need Python 2.5 or higher to get started, so be sure to have an
up-to-date Python 2.x installation.  At the time of writing, the WSGI
specification has not yet been finalized for Python 3, so Flask cannot support
the 3.x series of Python.

.. _virtualenv:

virtualenv
----------

Virtualenv is probably what you want to use during development, and if you have
shell access to your production machines, you'll probably want to use it there,
too.

What problem does virtualenv solve?  If you like Python as much as I do,
chances are you want to use it for other projects besides Flask-based web
applications.  But the more projects you have, the more likely it is that you
will be working with different versions of Python itself, or at least different
versions of Python libraries.  Let's face it: quite often libraries break
backwards compatibility, and it's unlikely that any serious application will
have zero dependencies.  So what do you do if two or more of your projects have
conflicting dependencies?

Virtualenv to the rescue!  Virtualenv enables multiple side-by-side
installations of Python, one for each project.  It doesn't actually install
separate copies of Python, but it does provide a clever way to keep different
project environments isolated.  Let's see how virtualenv works.

If you are on Mac OS X or Linux, chances are that one of the following two
commands will work for you::

    $ sudo easy_install virtualenv

or even better::

    $ sudo pip install virtualenv

One of these will probably install virtualenv on your system.  Maybe it's even
in your package manager.  If you use Ubuntu, try::

    $ sudo apt-get install python-virtualenv

If you are on Windows and don't have the `easy_install` command, you must
install it first.  Check the :ref:`windows-easy-install` section for more
information about how to do that.  Once you have it installed, run the same
commands as above, but without the `sudo` prefix.

Once you have virtualenv installed, just fire up a shell and create
your own environment.  I usually create a project folder and a `venv`
folder within::

    $ mkdir myproject
    $ cd myproject
    $ virtualenv venv
    New python executable in venv/bin/python
    Installing distribute............done.

Now, whenever you want to work on a project, you only have to activate the
corresponding environment.  On OS X and Linux, do the following::

    $ . venv/bin/activate

If you are a Windows user, the following command is for you::

    $ venv\scripts\activate

Either way, you should now be using your virtualenv (notice how the prompt of
your shell has changed to show the active environment).

Now you can just enter the following command to get Flask activated in your
virtualenv::

    $ pip install Flask

A few seconds later and you are good to go.


System-Wide Installation
------------------------

This is possible as well, though I do not recommend it.  Just run
`pip` with root privileges::

    $ sudo pip install Flask

(On Windows systems, run it in a command-prompt window with administrator
privileges, and leave out `sudo`.)


Living on the Edge
------------------

If you want to work with the latest version of Flask, there are two ways: you
can either let `pip` pull in the development version, or you can tell
it to operate on a git checkout.  Either way, virtualenv is recommended.

Get the git checkout in a new virtualenv and run in development mode::

    $ git clone http://github.com/mitsuhiko/flask.git
    Initialized empty Git repository in ~/dev/flask/.git/
    $ cd flask
    $ virtualenv venv --distribute
    New python executable in venv/bin/python
    Installing distribute............done.
    $ . venv/bin/activate
    $ python setup.py develop
    ...
    Finished processing dependencies for Flask

This will pull in the dependencies and activate the git head as the current
version inside the virtualenv.  Then all you have to do is run ``git pull
origin`` to update to the latest version.

To just get the development version without git, do this instead::

    $ mkdir flask
    $ cd flask
    $ virtualenv venv --distribute
    $ . venv/bin/activate
    New python executable in venv/bin/python
    Installing distribute............done.
    $ pip install Flask==dev
    ...
    Finished processing dependencies for Flask==dev

.. _windows-easy-install:

`pip` and `distribute` on Windows
-----------------------------------

On Windows, installation of `easy_install` is a little bit trickier, but still
quite easy.  The easiest way to do it is to download the
`distribute_setup.py`_ file and run it.  The easiest way to run the file is to
open your downloads folder and double-click on the file.

Next, add the `easy_install` command and other Python scripts to the
command search path, by adding your Python installation's Scripts folder
to the `PATH` environment variable.  To do that, right-click on the
"Computer" icon on the Desktop or in the Start menu, and choose "Properties".
Then click on "Advanced System settings" (in Windows XP, click on the
"Advanced" tab instead).  Then click on the "Environment variables" button.
Finally, double-click on the "Path" variable in the "System variables" section,
and add the path of your Python interpreter's Scripts folder. Be sure to
delimit it from existing values with a semicolon.  Assuming you are using
Python 2.7 on the default path, add the following value::


    ;C:\Python27\Scripts

And you are done!  To check that it worked, open the Command Prompt and execute
``easy_install``.  If you have User Account Control enabled on Windows Vista or
Windows 7, it should prompt you for administrator privileges.

Now that you have ``easy_install``, you can use it to install ``pip``::

    > easy_install pip


.. _distribute_setup.py: http://python-distribute.org/distribute_setup.py
