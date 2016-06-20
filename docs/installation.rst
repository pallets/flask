.. _installation:

Installation
============

Flask depends on some external libraries, like `Werkzeug
<http://werkzeug.pocoo.org/>`_ and `Jinja2 <http://jinja.pocoo.org/>`_.
Werkzeug is a toolkit for WSGI, the standard Python interface between web
applications and a variety of servers for both development and deployment.
Jinja2 renders templates.

So how do you get all that on your computer quickly?  There are many ways you
could do that, but the most kick-ass method is virtualenv, so let's have a look
at that first.

You will need Python 2.6 or newer to get started, so be sure to have an
up-to-date Python 2.x installation.  For using Flask with Python 3 have a
look at :ref:`python3-support`.

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

If you are on Mac OS X or Linux, chances are that the following
command will work for you::

    $ sudo pip install virtualenv

It will probably install virtualenv on your system.  Maybe it's even
in your package manager.  If you use Ubuntu, try::

    $ sudo apt-get install python-virtualenv

If you are on Windows and don't have the ``easy_install`` command, you must
install it first.  Check the :ref:`windows-easy-install` section for more
information about how to do that.  Once you have it installed, run the same
commands as above, but without the ``sudo`` prefix.

Once you have virtualenv installed, just fire up a shell and create
your own environment.  I usually create a project folder and a :file:`venv`
folder within::

    $ mkdir myproject
    $ cd myproject
    $ virtualenv venv
    New python executable in venv/bin/python
    Installing setuptools, pip............done.

Now, whenever you want to work on a project, you only have to activate the
corresponding environment.  On OS X and Linux, do the following::

    $ . venv/bin/activate

If you are a Windows user, the following command is for you::

    $ venv\scripts\activate

Either way, you should now be using your virtualenv (notice how the prompt of
your shell has changed to show the active environment).

And if you want to go back to the real world, use the following command::

    $ deactivate

After doing this, the prompt of your shell should be as familiar as before.

Now, let's move on. Enter the following command to get Flask activated in your
virtualenv::

    $ pip install Flask

A few seconds later and you are good to go.


System-Wide Installation
------------------------

This is possible as well, though I do not recommend it.  Just run
``pip`` with root privileges::

    $ sudo pip install Flask

(On Windows systems, run it in a command-prompt window with administrator
privileges, and leave out ``sudo``.)


Living on the Edge
------------------

If you want to work with the latest version of Flask, there are two ways: you
can either let ``pip`` pull in the development version, or you can tell
it to operate on a git checkout.  Either way, virtualenv is recommended.

Get the git checkout in a new virtualenv and run in development mode::

    $ git clone http://github.com/pallets/flask.git
    Initialized empty Git repository in ~/dev/flask/.git/
    $ cd flask
    $ virtualenv venv
    New python executable in venv/bin/python
    Installing setuptools, pip............done.
    $ . venv/bin/activate
    $ python setup.py develop
    ...
    Finished processing dependencies for Flask

This will pull in the dependencies and activate the git head as the current
version inside the virtualenv.  Then all you have to do is run ``git pull
origin`` to update to the latest version.

.. _windows-easy-install:

`pip` and `setuptools` on Windows
---------------------------------

Sometimes getting the standard "Python packaging tools" like ``pip``, ``setuptools``
and ``virtualenv`` can be a little trickier, but nothing very hard. The crucial
package you will need is pip - this will let you install
anything else (like virtualenv). Fortunately there is a "bootstrap script"
you can run to install.

If you don't currently have ``pip``, then `get-pip.py` will install it for you.

`get-pip.py`_

It should be double-clickable once you download it. If you already have ``pip``,
you can upgrade them by running::

    > pip install --upgrade pip setuptools

Most often, once you pull up a command prompt you want to be able to type ``pip``
and ``python`` which will run those things, but this might not automatically happen
on Windows, because it doesn't know where those executables are (give either a try!).

To fix this, you should be able to navigate to your Python install directory
(e.g :file:`C:\Python27`), then go to :file:`Tools`, then :file:`Scripts`, then find the
:file:`win_add2path.py` file and run that. Open a **new** Command Prompt and
check that you can now just type ``python`` to bring up the interpreter.

Finally, to install `virtualenv`_, you can simply run::

    > pip install virtualenv

Then you can be off on your way following the installation instructions above.

.. _get-pip.py: https://bootstrap.pypa.io/get-pip.py
