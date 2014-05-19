.. _tutorial-folders:

Step 0: Creating The Folders
============================

Before we get started, let's create the folders needed for this
application::

    /flaskr
        /static
        /templates

The `flaskr` folder is not a python package, but just somewhere we can
drop our files.  We will put our database schema and the main module
into this folder.  The files inside the `static` folder are available
to users of the application via `HTTP`.  This is where css and
javascript files go.  The `templates` folder is where Flask will look
for `Jinja2`_ templates.  The templates you create later in the
tutorial will go in this directory.

Continue with :ref:`tutorial-schema`.

.. _Jinja2: http://jinja.pocoo.org/
