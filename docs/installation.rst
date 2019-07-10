.. _installation:

Installation
============

Python Version
--------------

We recommend using the latest version of Python 3. Flask supports Python 3.5
and newer, Python 2.7, and PyPy.

Dependencies
------------

These distributions will be installed automatically when installing Flask.

* `Werkzeug`_ implements WSGI, the standard Python interface between
  applications and servers.
* `Jinja`_ is a template language that renders the pages your application
  serves.
* `MarkupSafe`_ comes with Jinja. It escapes untrusted input when rendering
  templates to avoid injection attacks.
* `ItsDangerous`_ securely signs data to ensure its integrity. This is used
  to protect Flask's session cookie.
* `Click`_ is a framework for writing command line applications. It provides
  the ``flask`` command and allows adding custom management commands.

.. _Werkzeug: https://palletsprojects.com/p/werkzeug/
.. _Jinja: https://palletsprojects.com/p/jinja/
.. _MarkupSafe: https://palletsprojects.com/p/markupsafe/
.. _ItsDangerous: https://palletsprojects.com/p/itsdangerous/
.. _Click: https://palletsprojects.com/p/click/

Optional dependencies
~~~~~~~~~~~~~~~~~~~~~

These distributions will not be installed automatically. Flask will detect and
use them if you install them.

* `Blinker`_ provides support for :ref:`signals`.
* `SimpleJSON`_ is a fast JSON implementation that is compatible with
  Python's ``json`` module. It is preferred for JSON operations if it is
  installed.
* `python-dotenv`_ enables support for :ref:`dotenv` when running ``flask``
  commands.
* `Watchdog`_ provides a faster, more efficient reloader for the development
  server.

.. _Blinker: https://pythonhosted.org/blinker/
.. _SimpleJSON: https://simplejson.readthedocs.io/
.. _python-dotenv: https://github.com/theskumar/python-dotenv#readme
.. _watchdog: https://pythonhosted.org/watchdog/

Virtual environments
--------------------

Use a virtual environment to manage the dependencies for your project, both in
development and in production.

What problem does a virtual environment solve? The more Python projects you
have, the more likely it is that you need to work with different versions of
Python libraries, or even Python itself. Newer versions of libraries for one
project can break compatibility in another project.

Virtual environments are independent groups of Python libraries, one for each
project. Packages installed for one project will not affect other projects or
the operating system's packages.

Python 3 comes bundled with the :mod:`venv` module to create virtual
environments. If you're using a modern version of Python, you can continue on
to the next section.

If you're using Python 2, see :ref:`install-install-virtualenv` first.

.. _install-create-env:

Create an environment
~~~~~~~~~~~~~~~~~~~~~

Create a project folder and a :file:`venv` folder within:

.. code-block:: sh

    $ mkdir myproject
    $ cd myproject
    $ python3 -m venv venv

On Windows:

.. code-block:: bat

    $ py -3 -m venv venv

If you needed to install virtualenv because you are using Python 2, use
the following command instead:

.. code-block:: sh

    $ python2 -m virtualenv venv

On Windows:

.. code-block:: bat

    > \Python27\Scripts\virtualenv.exe venv

.. _install-activate-env:

Activate the environment
~~~~~~~~~~~~~~~~~~~~~~~~

Before you work on your project, activate the corresponding environment:

.. code-block:: sh

    $ . venv/bin/activate

On Windows:

.. code-block:: bat

    > venv\Scripts\activate

Your shell prompt will change to show the name of the activated environment.

Install Flask
-------------

Within the activated environment, use the following command to install Flask:

.. code-block:: sh

    $ pip install Flask

Flask is now installed. Check out the :doc:`/quickstart` or go to the
:doc:`Documentation Overview </index>`.

Living on the edge
~~~~~~~~~~~~~~~~~~

If you want to work with the latest Flask code before it's released, install or
update the code from the master branch:

.. code-block:: sh

    $ pip install -U https://github.com/pallets/flask/archive/master.tar.gz

.. _install-install-virtualenv:

Install virtualenv
------------------

If you are using Python 2, the venv module is not available. Instead,
install `virtualenv`_.

On Linux, virtualenv is provided by your package manager:

.. code-block:: sh

    # Debian, Ubuntu
    $ sudo apt-get install python-virtualenv

    # CentOS, Fedora
    $ sudo yum install python-virtualenv

    # Arch
    $ sudo pacman -S python-virtualenv

If you are on Mac OS X or Windows, download `get-pip.py`_, then:

.. code-block:: sh

    $ sudo python2 Downloads/get-pip.py
    $ sudo python2 -m pip install virtualenv

On Windows, as an administrator:

.. code-block:: bat

    > \Python27\python.exe Downloads\get-pip.py
    > \Python27\python.exe -m pip install virtualenv

Now you can return above and :ref:`install-create-env`.

.. _virtualenv: https://virtualenv.pypa.io/
.. _get-pip.py: https://bootstrap.pypa.io/get-pip.py
