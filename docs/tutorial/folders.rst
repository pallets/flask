.. _tutorial-folders:

Step 0: Creating The Folders
============================

Before we get started, let's create the folders needed for this
application::

    /flaskr
        /static
        /templates

The ``flaskr`` folder is not a Python package, but just something where we
drop our files. Later on, we will put our database schema as well as main
module into this folder. It is done in the following way. The files inside
the :file:`static` folder are available to users of the application via HTTP.
This is the place where CSS and Javascript files go.  Inside the
:file:`templates` folder, Flask will look for `Jinja2`_ templates.  The
templates you create later on in the tutorial will go in this directory.

Continue with :ref:`tutorial-schema`.

.. _Jinja2: http://jinja.pocoo.org/
