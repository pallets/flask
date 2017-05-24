.. _tutorial:

Tutorial
========

So, you want to develop an application with Python and Flask?  Here you have
the chance to learn by example.  In this tutorial, we will create a simple
microblogging application that only supports one user, allows the user to create
text-only entries, but has no feeds or comments.  

While very simple, this example application still features everything you need
to get started.  In addition to Flask, we will use SQLite as a database 
(SQLite is a module included with Python) so there is nothing else you need.

If you want the full source code in advance or for comparison, check out
the `example source`_.

.. _example source:
   https://github.com/pallets/flask/tree/master/examples/flaskr/

.. toctree::
   :maxdepth: 2

   introduction
   folders
   schema
   setup
   packaging
   dbcon
   dbinit
   views
   templates
   css
   testing
