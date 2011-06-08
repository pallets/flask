.. _blueprints:

Modular Applications with Blueprints
====================================

.. versionadded:: 0.7

Flask uses a concept of *blueprints* for making application components and
supporting common patterns within an application or across applications.
Blueprints can greatly simplify how large applications work and provide a
central means for Flask extensions to register operations on applications.
A :class:`Blueprint` object works similarly to a :class:`Flask`
application object, but it is not actually an application.  Rather it is a
*blueprint* of how to construct or extend an application.

Why Blueprints?
---------------

Blueprints in Flask are intended for these cases:

* Factor an application into a set of blueprints.  This is ideal for
  larger applications; a project could instantiate an application object,
  initialize several extensions, and register a collection of blueprints.
* Register a blueprint on an application at a URL prefix and/or subdomain.
  Paremeters in the URL prefix/subdomain become common view arguments
  (with defaults) across all view functions in the blueprint.
* Register a blueprint multiple times on an application with different URL
  rules.
* Provide template filters, static files, templates, and other utilities
  through blueprints.  A blueprint does not have to implement applications
  or view functions.
* Register a blueprint on an application for any of these cases when
  initializing a Flask extension.

A blueprint in Flask is not a pluggable app because it is not actually an
application -- it's a set of operations which can be registered on an
application, even multiple times.  Why not have multiple application
objects?  You can do that (see :ref:`app-dispatch`), but your applications
will have separate configs and will be managed at the WSGI layer.

Blueprints instead provide separation at the Flask level, share
application config, and can change an application object as necessary with
being registered. The downside is that you cannot unregister a blueprint
once application without having to destroy the whole application object.

The Concept of Blueprints
-------------------------

The basic concept of blueprints is that they record operations to execute
when registered on an application.  Flask associates view functions with
blueprints when dispatching requests and generating URLs from one endpoint
to another.

My First Blueprint
------------------

This is what a very basic blueprint looks like.  In this case we want to
implement a blueprint that does simple rendering of static templates::

    from flask import Blueprint, render_template, abort
    from jinja2 import TemplateNotFound

    simple_page = Blueprint('simple_page', __name__)

    @simple_page.route('/', defaults={'page': 'index'})
    @simple_page.route('/<page>')
    def show(page):
        try:
            return render_template('simple_pages/%s.html' % page)
        except TemplateNotFound:
            abort(404)
