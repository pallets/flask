.. _tutorial-introduction:

Introducing Flaskr
==================

We will call our blogging application flaskr, but feel free to choose a
less web-2.0-ish name ;)  Basically, we want it to do the following things:

1. Let the user sign in and out with credentials specified in the
   configuration.  Only one user is supported.
2. When the user is logged in, they can add new entries to the page
   consisting of a text-only title and some HTML for the text body.  This HTML
   is not sanitized because we trust the user here.
3. The page shows all entries so far in reverse order (newest on top), and
   the user can add new ones from there if they are logged in.

We will be using SQLite3 directly because it's good
enough for an application of this size.  For larger applications, however,
it makes a lot of sense to use `SQLAlchemy`_, which handles database
connections in a more intelligent way, allows you to target different
relational databases at once, and more.  You might also want to consider
one of the popular NoSQL databases if your data is more suited for those.

Here is a screenshot from the final application:

.. image:: ../_static/flaskr.png
   :align: center
   :class: screenshot
   :alt: screenshot of the final application

Continue with :ref:`tutorial-folders`.

.. _SQLAlchemy: http://www.sqlalchemy.org/
