.. _tutorial-folders:

Step 0: Creating The Folders
============================

It is recommended to install your Flask application within a virtualenv. Please
read the :ref:`installation` section to set up your environment.

Now that you have installed Flask, you will need to create the folders required
for this tutorial. Your directory structure will look like this::

    /flaskr
        /flaskr
            /static
            /templates

The application will be installed and run as Python package.  This is the
recommended way to install and run Flask applications.  You will see exactly
how to run ``flaskr`` later on in this tutorial.

For now go ahead and create the applications directory structure.  In the next
few steps you will be creating the database schema as well as the main module.

As a quick side note, the files inside of the :file:`static` folder are
available to users of the application via HTTP.  This is the place where CSS and
JavaScript files go.  Inside the :file:`templates` folder, Flask will look for
`Jinja2`_ templates.  You will see examples of this later on.

For now you should continue with :ref:`tutorial-schema`.

.. _Jinja2: http://jinja.pocoo.org/
