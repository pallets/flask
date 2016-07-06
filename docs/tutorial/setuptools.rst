.. _tutorial-setuptools:

Step 3: Installing flaskr with setuptools
=========================================

Flask is now shipped with built-in support for `Click`_.  Click provides
Flask with enhanced and extensible command line utilities.  Later in this
tutorial you will see exactly how to extend the ``flask`` command line
interface (CLI).

A useful pattern to manage a Flask application is to install your app
using `setuptools`_.  This involves creating a :file:`setup.py`
in the projects root directory.  You also need to add an empty
:file:`__init__.py` file to make the :file:`flaskr/flaskr` directory
a package.  The code structure at this point should be::

    /flaskr
        /flaskr
            __init__.py
            /static
            /templates
        setup.py

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

At this point you should be able to install the application.  As usual, it
is recommended to install your Flask application within a `virtualenv`_.
With that said, go ahead and install the application with::

    pip install --editable .

.. note:: The above installation command assumes that it is run within the
    projects root directory, `flaskr/`.  Also, the `editable` flag allows
    editing source code without having to reinstall the Flask app each time
    you make changes.

With that out of the way, you should be able to start up the application.
Do this with the following commands::

    export FLASK_APP=flaskr.flaskr
    export FLASK_DEBUG=1
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
.. _setuptools: https://setuptools.readthedocs.io
.. _virtualenv: https://virtualenv.pypa.io
