.. _tutorial:

Tutorial
========

.. toctree::
    :caption: Contents:
    :maxdepth: 1

    layout
    factory
    database
    views
    templates
    static
    blog
    install
    tests
    deploy
    next

This tutorial will walk you through creating a basic blog application
called Flaskr, where users will be able to register, log in, create posts,
and edit or delete their own posts. You will be able to package and
install the application on other computers.

.. image:: flaskr_index.png
    :align: center
    :class: screenshot
    :alt: screenshot of index page

You must be familiar with Python first. Refer to the `official
tutorial`_ in the Python docs if needed.

.. _official tutorial: https://docs.python.org/3/tutorial/

Even though this tutorial is designed to give a good starting point, it doesn't
cover all of Flask's features. Check out the :ref:`quickstart` for an
overview of what Flask can do, and then dive into the docs to find out more.
The tutorial only uses what's provided by Flask and Python. In another
project, you might decide to use :ref:`extensions` or other libraries to
make some tasks simpler.

.. image:: flaskr_login.png
    :align: center
    :class: screenshot
    :alt: screenshot of login page

Flask is flexible. It doesn't require you to use any particular project
or code layout. However, when first starting, it's helpful to use a structured approach.
This means that the tutorial will require a bit of
boilerplate up front, but this boilerplate is done to avoid common pitfalls that
new developers encounter. This tutorial creates a project that's easy to expand. 
Once you become more comfortable with Flask, you can step out of
this structure and take full advantage of Flask's flexibility.

.. image:: flaskr_edit.png
    :align: center
    :class: screenshot
    :alt: screenshot of login page

:gh:`The tutorial project is available as an example in the Flask
repository <examples/tutorial>`, if you want to compare your project
with the final product as you follow the tutorial.

Continue to :doc:`layout`.
