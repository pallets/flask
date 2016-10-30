.. _tutorial-packaging:

Step 3: Installing flaskr as a Package
======================================

Flask is now shipped with built-in support for `Click`_.  Click provides
Flask with enhanced and extensible command line utilities.  Later in this
tutorial you will see exactly how to extend the ``flask`` command line
interface (CLI).

A useful pattern to manage a Flask application is to install your app
following the `Python Packaging Guide`_.  Presently this involves 
creating two new files; :file:`setup.py` and :file:`MANIFEST.in` in the 
projects root directory.  You also need to add an :file:`__init__.py` 
file to make the :file:`flaskr/flaskr` directory a package.  After these 
changes, your code structure should be::

    /flaskr
        /flaskr
            __init__.py
            /static
            /templates
            flaskr.py
            schema.sql
        setup.py
        MANIFEST.in

The content of the ``setup.py`` file for ``flaskr`` is:

.. sourcecode:: python

    from setuptools import setup

    setup(
        name='flaskr',
        packages=['flaskr'],
        include_package_data=True,
        install_requires=[
            'flask',
        ],
    )

When using setuptools, it is also necessary to specify any special files
that should be included in your package (in the :file:`MANIFEST.in`).
In this case, the static and templates directories need to be included,
as well as the schema. Create the :file:`MANIFEST.in` and add the
following lines::

    graft flaskr/templates
    graft flaskr/static
    include flaskr/schema.sql

To simplify locating the application, add the following import statement 
into this file, :file:`flaskr/__init__.py`:

.. sourcecode:: python

    from .flaskr import app

This import statement brings the application instance into the top-level 
of the application package.  When it is time to run the application, the 
Flask development server needs the location of the app instance.  This 
import statement simplifies the location process.  Without it the export 
statement a few steps below would need to be 
``export FLASK_APP=flaskr.flaskr``.

At this point you should be able to install the application.  As usual, it
is recommended to install your Flask application within a `virtualenv`_.
With that said, go ahead and install the application with::

    pip install --editable .

The above installation command assumes that it is run within the projects 
root directory, `flaskr/`.  The `editable` flag allows editing 
source code without having to reinstall the Flask app each time you make 
changes.  The flaskr app is now installed in your virtualenv (see output 
of ``pip freeze``).

With that out of the way, you should be able to start up the application.
Do this with the following commands::

    export FLASK_APP=flaskr
    export FLASK_DEBUG=true
    flask run

(In case you are on Windows you need to use `set` instead of `export`).
The :envvar:`FLASK_DEBUG` flag enables or disables the interactive debugger.
*Never leave debug mode activated in a production system*, because it will
allow users to execute code on the server!

You will see a message telling you that server has started along with
the address at which you can access it.

When you head over to the server in your browser, you will get a 404 error
because we don't have any views yet.  That will be addressed a little later,
but first, you should get the database working.

.. admonition:: Externally Visible Server

   Want your server to be publicly available?  Check out the
   :ref:`externally visible server <public-server>` section for more
   information.

Continue with :ref:`tutorial-dbcon`.

.. _Click: http://click.pocoo.org
.. _Python Packaging Guide: https://packaging.python.org
.. _virtualenv: https://virtualenv.pypa.io
