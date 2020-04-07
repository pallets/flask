Installation
============


Python Version
--------------

We recommend using the latest version of Python. Flask supports Python
3.6 and newer.


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

* `Blinker`_ provides support for :doc:`signals`.
* `python-dotenv`_ enables support for :ref:`dotenv` when running ``flask``
  commands.
* `Watchdog`_ provides a faster, more efficient reloader for the development
  server.

.. _Blinker: https://pythonhosted.org/blinker/
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

Python comes bundled with the :mod:`venv` module to create virtual
environments.


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


.. _install-activate-env:

Activate the environment
~~~~~~~~~~~~~~~~~~~~~~~~

Before you work on your project, activate the corresponding environment:

.. code-block:: sh

    $ . venv/bin/activate

On Windows:

.. code-block:: bat

    > venv\Scripts\activate

Your shell prompt will change to show the name of the activated
environment.


Install Flask
-------------

Within the activated environment, use the following command to install
Flask:

.. code-block:: sh

    $ pip install Flask

Flask is now installed. Check out the :doc:`/quickstart` or go to the
:doc:`Documentation Overview </index>`.
