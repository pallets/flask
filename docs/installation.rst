.. _installation:

Installation
============

Flask depends on two external libraries, `Werkzeug
<http://werkzeug.pocoo.org/>`_ and `Jinja2 <http://jinja.pocoo.org/2/>`_.
Werkzeug is a toolkit for WSGI, the standard Python interface between web
applications and a variety of servers for both development and deployment.
Jinja2 renders templates.

So how do you get all that on your computer quickly?  There are many ways
which this section will explain, but the most kick-ass method is
virtualenv, so let's look at that first.

.. _virtualenv:

virtualenv
----------

Virtualenv is probably what you want to use during development, and in
production too if you have shell access there.

What problem does virtualenv solve?  If you like Python as I do,
chances are you want to use it for other projects besides Flask-based
web applications.  But the more projects you have, the more likely it is
that you will be working with different versions of Python itself, or at
least different versions of Python libraries.  Let's face it; quite often
libraries break backwards compatibility, and it's unlikely that any serious
application will have zero dependencies.  So what do you do if two or more
of your projects have conflicting dependencies?

Virtualenv to the rescue!  It basically enables multiple side-by-side
installations of Python, one for each project.  It doesn't actually
install separate copies of Python, but it does provide a clever way
to keep different project environments isolated.

So let's see how virtualenv works!

If you are on Mac OS X or Linux, chances are that one of the following two
commands will work for you::

    $ sudo easy_install virtualenv

or even better::

    $ sudo pip install virtualenv

One of these will probably install virtualenv on your system.  Maybe it's
even in your package manager.  If you use Ubuntu, try::

    $ sudo apt-get install python-virtualenv

If you are on Windows and don't have the `easy_install` command, you must
install it first.  Check the :ref:`windows-easy-install` section for more
information about how to do that.  Once you have it installed, run the
same commands as above, but without the `sudo` prefix.

Once you have virtualenv installed, just fire up a shell and create
your own environment.  I usually create a project folder and an `env`
folder within::

    $ mkdir myproject
    $ cd myproject
    $ virtualenv env
    New python executable in env/bin/python
    Installing setuptools............done.

Now, whenever you want to work on a project, you only have to activate
the corresponding environment.  On OS X and Linux, do the following::

    $ . env/bin/activate

(Note the space between the dot and the script name.  The dot means that
this script should run in the context of the current shell.  If this command
does not work in your shell, try replacing the dot with ``source``)

If you are a Windows user, the following command is for you::

    $ env\scripts\activate

Either way, you should now be using your virtualenv (see how the prompt of
your shell has changed to show the virtualenv).

Now you can just enter the following command to get Flask activated in
your virtualenv::

    $ easy_install Flask

A few seconds later you are good to go.


System Wide Installation
------------------------

This is possible as well, but I do not recommend it.  Just run
`easy_install` with root rights::

    $ sudo easy_install Flask

(Run it in an Admin shell on Windows systems and without `sudo`).


Living on the Edge
------------------

If you want to work with the latest version of Flask, there are two ways: you
can either let `easy_install` pull in the development version, or tell it
to operate on a git checkout.  Either way, virtualenv is recommended.

Get the git checkout in a new virtualenv and run in development mode::

    $ git clone http://github.com/mitsuhiko/flask.git
    Initialized empty Git repository in ~/dev/flask/.git/
    $ cd flask
    $ virtualenv env
    $ . env/bin/activate
    New python executable in env/bin/python
    Installing setuptools............done.
    $ python setup.py develop
    ...
    Finished processing dependencies for Flask

This will pull in the dependencies and activate the git head as the current
version inside the virtualenv.  Then you just have to ``git pull origin``
to get the latest version.

To just get the development version without git, do this instead::

    $ mkdir flask
    $ cd flask
    $ virtualenv env
    $ . env/bin/activate
    New python executable in env/bin/python
    Installing setuptools............done.
    $ easy_install Flask==dev
    ...
    Finished processing dependencies for Flask==dev

.. _windows-easy-install:

`easy_install` on Windows
-------------------------

On Windows, installation of `easy_install` is a little bit tricker because
slightly different rules apply on Windows than on Unix-like systems, but
it's not difficult.  The easiest way to do it is to download the
`ez_setup.py`_ file and run it.  The easiest way to run the file is to
open your downloads folder and double-click on the file.

Next, add the `easy_install` command and other Python scripts to the
command search path, by adding your Python installation's Scripts folder
to the `PATH` environment variable.  To do that, right-click on the
"Computer" icon on the Desktop or in the Start menu, and choose
"Properties".  Then, on Windows Vista and Windows 7 click on "Advanced System
settings"; on Windows XP, click on the "Advanced" tab instead.  Then click
on the "Environment variables" button and double click on the "Path"
variable in the "System variables" section.  There append the path of your
Python interpreter's Scripts folder; make sure you delimit it from
existing values with a semicolon.  Assuming you are using Python 2.6 on
the default path, add the following value::

    ;C:\Python26\Scripts

Then you are done.  To check that it worked, open the Command Prompt and
execute ``easy_install``.  If you have User Account Control enabled on
Windows Vista or Windows 7, it should prompt you for admin privileges.


.. _ez_setup.py: http://peak.telecommunity.com/dist/ez_setup.py
