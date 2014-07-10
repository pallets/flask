.. _tutorial:

Tutorial
========

You want to develop an application with Python and Flask?  Here you have
the chance to learn that by example.  In this tutorial we will create a
simple microblog application.  It only supports one user that can create
text-only entries and there are no feeds or comments, but it still
features everything you need to get started.  We will use Flask and SQLite
as database which comes out of the box with Python, so there is nothing
else you need.

If you want the full sourcecode in advance or for comparison, check out
the `example source`_.  If you are using the latest stable release of
Flask (0.10.1), the above source will not work, and you should instead use
the `source from that release`_.

.. _example source:
   http://github.com/mitsuhiko/flask/tree/master/examples/flaskr/
   
.. _source from that release:
   http://github.com/mitsuhiko/flask/tree/298334fffc8288b5a9a45ef4150e3c4292e45318/examples/flaskr

.. toctree::
   :maxdepth: 2

   introduction
   folders
   schema
   setup
   dbcon
   dbinit
   views
   templates
   css
   testing
