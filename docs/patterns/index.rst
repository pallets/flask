Patterns for Flask
==================

Certain features and interactions are common enough that you will find
them in most web applications. For example, many applications use a
relational database and user authentication. They will open a database
connection at the beginning of the request and get the information for
the logged in user. At the end of the request, the database connection
is closed.

These types of patterns may be a bit outside the scope of Flask itself,
but Flask makes it easy to implement them. Some common patterns are
collected in the following pages.

.. toctree::
   :maxdepth: 2

   packages
   appfactories
   appdispatch
   urlprocessors
   distribute
   fabric
   sqlite3
   sqlalchemy
   fileuploads
   caching
   viewdecorators
   wtforms
   templateinheritance
   flashing
   jquery
   lazyloading
   mongoengine
   favicon
   streaming
   deferredcallbacks
   methodoverrides
   requestchecksum
   celery
   subclassing
   singlepageapplications
