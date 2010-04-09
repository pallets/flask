.. _installation:

Installation
============

Flask is a microframework and yet it depends on external libraries.  There
are various ways how you can install that library and this explains each
way and why there are multiple ways.

Flask depends on two external libraries: `Werkzeug
<http://werkzeug.pocoo.org/>`_ and `Jinja2 <http://jinja.pocoo.org/2/>`_.
The first on is responsible for interfacing WSGI the latter to render
templates.  Now you are maybe asking, what is WSGI?  WSGI is a standard
in Python that is basically responsible for ensuring that your application
is behaving in a specific way that you can run it on different
environments (for example on a local development server, on an Apache2, on
lighttpd, on Google's appengine or whatever you have in mind).

So how do you get all that on your computer in no time?  The most kick-ass
method is virtualenv, so let's look at that first.

virtualenv
----------

Virtualenv is what you want to use during development and in production if
you have shell access.  So first: what does virtualenv do?  If you are
like me and you like Python, chances are you want to use it for another
project as well.  Now the more projects you have, the more likely it is
that you will be working with different versions of Python itself or a
library involved.  Because let's face it: quite often libraries break
backwards compatibility and it's unlikely that your application will
not have any dependencies, that just won't happen.  So virtualenv for the
rescue!

It basically makes it possible to have multiple side-by-side
"installations" of Python, each for your own project.  It's not actually
an installation but a clever way to keep things separated.

So let's see how that works!

If you are on OS X or Linux chances are that one of the following two
commands will for for you::

    sudo easy_install virtualenv

or even better::

    sudo pip install virtualenv

Changes are you have virtualenv installed on your system then.  Maybe it's
even in your package manager (on ubuntu try ``sudo apt-get install
python-virtualenv``).

On windows, just installed virtualenv from the `Python Package Index
<http://pypi.python.org/pypi/virtualenv>`_.

So now that you have virtualenv running just fire up a shell and create
your own environment.  I usually create a folder and a `env` folder
within::

    $ mkdir myproject
    $ cd myproject
    $ virtualenv env
    New python executable in env/bin/python
    Installing setuptools............done.

Now you only have to activate it, whenever you work with it.  On OS X and
Linux do the following::

    $ source env/bin/activate

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

This is possible as well, but I would not recommend it.  Just run
`easy_install` with root rights::

    sudo easy_install Flask

(Run it in an Admin shell on Windows systems and without the `sudo`). 


The Drop into Place Version
---------------------------

Now I really don't recommend this way on using Flask, but you can do that
of course as well.  Download the `dip` zipfile from the website and unzip
it next to your application.
