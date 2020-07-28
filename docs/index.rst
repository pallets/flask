.. rst-class:: hide-header

Welcome to Flask
================

.. image:: _static/flask-logo.png
    :alt: Flask: web development, one drop at a time
    :align: center
    :target: https://palletsprojects.com/p/flask/

Welcome to Flask's documentation. Get started with :doc:`installation`
and then get an overview with the :doc:`quickstart`. There is also a
more detailed :doc:`tutorial/index` that shows how to create a small but
complete application with Flask. Common patterns are described in the
:doc:`patterns/index` section. The rest of the docs describe each
component of Flask in detail, with a full reference in the :doc:`api`
section.

Flask depends on the `Jinja`_ template engine and the `Werkzeug`_ WSGI
toolkit. The documentation for these libraries can be found at:

- `Jinja documentation <https://jinja.palletsprojects.com/>`_
- `Werkzeug documentation <https://werkzeug.palletsprojects.com/>`_

.. _Jinja: https://www.palletsprojects.com/p/jinja/
.. _Werkzeug: https://www.palletsprojects.com/p/werkzeug/


User's Guide
------------

This part of the documentation, which is mostly prose, begins with some
background information about Flask, then focuses on step-by-step
instructions for web development with Flask.

.. toctree::
   :maxdepth: 2

   foreword
   advanced_foreword
   installation
   quickstart
   tutorial/index
   templating
   testing
   errorhandling
   debugging
   logging
   config
   signals
   views
   appcontext
   reqcontext
   blueprints
   extensions
   cli
   server
   shell
   patterns/index
   deploying/index
   becomingbig


API Reference
-------------

If you are looking for information on a specific function, class or
method, this part of the documentation is for you.

.. toctree::
   :maxdepth: 2

   api


Additional Notes
----------------

Design notes, legal information and changelog are here for the interested.

.. toctree::
   :maxdepth: 2

   design
   htmlfaq
   security
   extensiondev
   changelog
   license
   contributing
