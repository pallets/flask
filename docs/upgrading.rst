Upgrading to Newer Releases
===========================

Flask itself is changing like any software is changing over time.  Most of
the changes are the nice kind, the kind where you don't have th change
anything in your code to profit from a new release.

However every once in a while there are changes that do require some
changes in your code or there are changes that make it possible for you to
improve your own code quality by taking advantage of new features in
Flask.

This section of the documentation enumerates all the changes in Flask from
release to release and how you can change your code to have a painless
updating experience.

If you want to use the `easy_install` command to upgrade your Flask
installation, make sure to pass it the ``-U`` parameter::

    $ easy_install -U Flask

Version 0.6
-----------

Flask 0.6 comes with a backwards incompatible change which affects the
order of after-request handlers.  Previously they were called in the order
of the registration, now they are called in reverse order.  This change
was made so that Flask behaves more like people expected it to work and
how other systems handle request pre- and postprocessing.  If you
dependend on the order of execution of post-request functions, be sure to
change the order.

Another change that breaks backwards compatibility is that context
processors will no longer override values passed directly to the template
rendering function.  If for example `request` is as variable passed
directly to the template, the default context processor will not override
it with the current request object.  This makes it easier to extend
context processors later to inject additional variables without breaking
existing template not expecting them.

Version 0.5
-----------

Flask 0.5 is the first release that comes as a Python package instead of a
single module.  There were a couple of internal refactoring so if you
depend on undocumented internal details you probably have to adapt the
imports.

The following changes may be relevant to your application:

-   autoescaping no longer happens for all templates.  Instead it is
    configured to only happen on files ending with ``.html``, ``.htm``,
    ``.xml`` and ``.xhtml``.  If you have templates with different
    extensions you should override the
    :meth:`~flask.Flask.select_jinja_autoescape` method.
-   Flask no longer supports zipped applications in this release.  This
    functionality might come back in future releases if there is demand
    for this feature.  Removing support for this makes the Flask internal
    code easier to understand and fixes a couple of small issues that make
    debugging harder than necessary.
-   The `create_jinja_loader` function is gone.  If you want to customize
    the Jinja loader now, use the
    :meth:`~flask.Flask.create_jinja_environment` method instead.

Version 0.4
-----------

For application developers there are no changes that require changes in
your code.  In case you are developing on a Flask extension however, and
that extension has a unittest-mode you might want to link the activation
of that mode to the new ``TESTING`` flag.

Version 0.3
-----------

Flask 0.3 introduces configuration support and logging as well as
categories for flashing messages.  All these are features that are 100%
backwards compatible but you might want to take advantage of them.

Configuration Support
`````````````````````

The configuration support makes it easier to write any kind of application
that requires some sort of configuration.  (Which most likely is the case
for any application out there).

If you previously had code like this::

    app.debug = DEBUG
    app.secret_key = SECRET_KEY

You no longer have to do that, instead you can just load a configuration
into the config object.  How this works is outlined in :ref:`config`.

Logging Integration
```````````````````

Flask now configures a logger for you with some basic and useful defaults.
If you run your application in production and want to profit from
automatic error logging, you might be interested in attaching a proper log
handler.  Also you can start logging warnings and errors into the logger
when appropriately.  For more information on that, read
:ref:`application-errors`.

Categories for Flash Messages
`````````````````````````````

Flash messages can now have categories attached.  This makes it possible
to render errors, warnings or regular messages differently for example.
This is an opt-in feature because it requires some rethinking in the code.

Read all about that in the :ref:`message-flashing-pattern` pattern.
