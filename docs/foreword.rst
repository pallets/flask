Foreword
========

Read this before you get started with Flask.  This hopefully answers some
questions about the purpose and goals of the project, and when you
should or should not be using it.

What does "micro" mean?
-----------------------

“Micro” does not mean that your whole web application has to fit into
a  single Python file (although it certainly can). Nor does it mean
that Flask is lacking in functionality. The "micro" in microframework
means Flask aims to keep the core simple but extensible. Flask won't make 
many decisions for you, such as what database to use. Those decisions that 
it does make, such as what templating engine to use, are easy to change. 
Everything else is up to you, so that Flask can be everything you need 
and nothing you don't.

By default, Flask does not include a database abstraction layer, form
validation or anything else where different libraries already exist that can
handle that. Instead, FLask extensions add such functionality to your
application as if it was implemented in Flask itself. Numerous extensions
provide database integration, form validation, upload handling, various open
authentication technologies, and more. Flask may be "micro", but the
possibilities are endless.

Convention over Configuration
-----------------------------

Flask is based on convention over configuration, which means that many things
are preconfigured. For example, by convention templates and static files are
stored in subdirectories within the application's Python source tree. While
this can be changed you usually don't have to. We want to minimize the time
you need to spend in order to get up and running, without assuming things 
about your needs.

Growing Up
----------

Since Flask is based on a very solid foundation there is not a lot of code in
Flask itself.  As such it's easy to adapt even for large applications and we
are making sure that you can either configure it as much as possible by
subclassing things or by forking the entire codebase.  If you are interested
in that, check out the :ref:`becomingbig` chapter.

If you are curious about the Flask design principles, head over to the section
about :ref:`design`.

For the Stalwart and Wizened...
-------------------------------

If you're more curious about the minutiae of Flask's implementation, and
whether its structure is right for your needs, read the
:ref:`advanced_foreword`.
