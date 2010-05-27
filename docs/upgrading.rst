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
