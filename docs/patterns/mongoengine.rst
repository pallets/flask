.. mongoengine-pattern:

MongoEngine in Flask
====================

Using a document database rather than a full DBMS gets more common these days.
This pattern shows how to use MongoEngine, a document mapper library, to
integrate with MongoDB.

This pattern requires a running MongoDB server, MongoEngine_ and Flask-MongoEngine_
libraries installed::

    pip install flask-mongoengine

.. _MongoEngine: http://mongoengine.org
.. _Flask-MongoEngine: http://docs.mongoengine.org/projects/flask-mongoengine/en/latest/>`_

Configuration
-------------

Basic setup can be done by defining ``MONGODB_SETTINGS`` on App config and then
creating a ``MongoEngine`` instance::

    from flask import Flask
    from flask_mongoengine import MongoEngine

    app = Flask(__name__)
    app.config['MONGODB_SETTINGS'] = {
        'host': "mongodb://localhost:27017/mydb"
    }
    db = MongoEngine(app)


Mapping Documents
-----------------

To declare models that will represent your Mongo documents, just create a class that
inherits from ``Document`` and declare each of the fields::

    from mongoengine import *


    class Movie(Document):

        title = StringField(required=True)
        year = IntField()
        rated = StringField()
        director = StringField()
        actors = ListField()

If the model has embedded documents, use ``EmbeddedDocument`` to defined the fields of
the embedded document and ``EmbeddedDocumentField`` to declare it on the parent document::

    class Imdb(EmbeddedDocument):

        imdb_id = StringField()
        rating = DecimalField()
        votes = IntField()


    class Movie(Document):

        ...
        imdb = EmbeddedDocumentField(Imdb)


Creating Data
-------------

Just create the objects and call ``save()``::

    bttf = Movie(title="Back To The Future", year=1985)
    bttf.actors = [
        "Michael J. Fox",
        "Christopher Lloyd"
    ]
    bttf.imdb = Imdb(imdb_id="tt0088763", rating=8.5)
    bttf.save()


Queries
-------

Use the class ``objects`` attribute to make queries::

    bttf = Movies.objects(title="Back To The Future").get()  # Throw error if not unique

``objects`` is an iterable. Query operators may be user by concatenating it with the document
key using a double-underscore::

    some_theron_movie = Movie.objects(actors__in=["Charlize Theron"]).first()

    for recents in Movie.objects(year__gte=2017):
        print(recents.title)

Available operators are as follows:

* ``ne`` -- not equal to
* ``lt`` -- less than
* ``lte`` -- less than or equal to
* ``gt`` -- greater than
* ``gte`` -- greater than or equal to
* ``not`` -- negate a standard check, may be used before other operators (e.g.
  ``Q(age__not__mod=5)``)
* ``in`` -- value is in list (a list of values should be provided)
* ``nin`` -- value is not in list (a list of values should be provided)
* ``mod`` -- ``value % x == y``, where ``x`` and ``y`` are two provided values
* ``all`` -- every item in list of values provided is in array
* ``size`` -- the size of the array is
* ``exists`` -- value for field exists

String queries
::::::::::::::

The following operators are available as shortcuts to querying with regular
expressions:

* ``exact`` -- string field exactly matches value
* ``iexact`` -- string field exactly matches value (case insensitive)
* ``contains`` -- string field contains value
* ``icontains`` -- string field contains value (case insensitive)
* ``startswith`` -- string field starts with value
* ``istartswith`` -- string field starts with value (case insensitive)
* ``endswith`` -- string field ends with value
* ``iendswith`` -- string field ends with value (case insensitive)
* ``match``  -- performs an $elemMatch so you can match an entire document within an array

Some Tips
---------

* Attributes can be set as ``unique``
* ``MongoEngine`` creates the ``_id`` attribute automatically to acess ``ObjectIds``
* You can add choices to string fields: ``StringField(choices=['Apple', 'Banana'])``
* If you don't want your class name to be the same name as the collection, you can define
  a ``meta`` class member and use the ``collection`` parameter::

    class Movie(Document):

        meta ={'collection': 'movie_documents'}

Accessing PyMongo MongoClient
-----------------------------

If, for some reason, you want to access PyMongo instance, use ``get_connection`` function::

    from mongoengine.connection import get_connection

    conn = get_connection()
    collection = conn.mydb.movie
    collection({'title': u'Days of Thunder'})

For more information about MongoEngine, head over to the
`website <http://docs.mongoengine.org/>`_.
