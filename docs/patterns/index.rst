.. _patterns:

Patterns for Flask
==================

Certain things are common enough that the changes are high you will find
them in most web applications.  For example quite a lot of applications
are using relational databases and user authentication.  In that case,
changes are they will open a database connection at the beginning of the
request and get the information of the currently logged in user.  At the
end of the request, the database connection is closed again.

.. toctree::
   :maxdepth: 2

   packages
   sqlite3
   sqlalchemy
   wtforms
   templateinheritance
   flashing
   jquery
