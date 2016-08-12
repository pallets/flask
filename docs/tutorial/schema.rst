.. _tutorial-schema:

Step 1: Database Schema
=======================

In this step, you will create the database schema.  Only a single table is
needed for this application and it will only support SQLite.  All you need to do
is put the following contents into a file named :file:`schema.sql` in the
:file:`flaskr/flaskr` folder:

.. sourcecode:: sql

    drop table if exists entries;
    create table entries (
      id integer primary key autoincrement,
      title text not null,
      'text' text not null
    );

This schema consists of a single table called ``entries``.  Each row in
this table has an ``id``, a ``title``, and a ``text``.  The ``id`` is an
automatically incrementing integer and a primary key, the other two are
strings that must not be null.

Continue with :ref:`tutorial-setup`.
