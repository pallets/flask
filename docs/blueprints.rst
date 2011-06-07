.. _blueprints:

Modular Applications with Blueprints
====================================

.. versionadded:: 0.7

Flask knows a concept known as “blueprints” which can greatly simplify how
large applications work.  A blueprint is an object works similar to an
actual :class:`Flask` application object, but it is not actually an
application.  Rather it is the blueprint of how to create an application.
Think of it like that: you might want to have an application that has a
wiki.  So what you can do is creating the blueprint for a wiki and then
let the application assemble the wiki on the application object.

Why Blueprints?
---------------

Why have blueprints and not multiple application objects?  The utopia of
pluggable applications are different WSGI applications and merging them
together somehow.  You can do that (see :ref:`app-dispatch`) but it's not
the right tool for every case.  Having different applications means having
different configs.  Applications are also separated on the WSGI layer
which is a lot lower level than the level that Flask usually operates on
where you have request and response objects.

Blueprints do not necessarily have to implement applications.  They could
only provide filters for templates, static files, templates or similar
things.  They share the same config as the application and can change the
application as necessary when being registered.

The downside is that you cannot unregister a blueprint once application
without having to destroy the whole application object.

The Concept of Blueprints
-------------------------

The basic concept of blueprints is that they record operations that should
be executed when the blueprint is registered on the application.  However
additionally each time a request gets dispatched to a view that was
declared to a blueprint Flask will remember that the request was
dispatched to that blueprint.  That way it's easier to generate URLs from
one endpoint to another in the same module.
