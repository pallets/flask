Foreword
========

Read this before you get started with Flask.  This hopefully answers some
questions about the intention of the project, what it aims at and when you
should or should not be using it.

What does Micro Mean?
---------------------

The micro in microframework for me means on the one hand being small in
size, complexity but on the other hand also that the complexity of the
applications that are written with these frameworks do not exceed a
certain size.  A microframework like Flask sacrifices a few things in
order to be approachable and to be as concise as possible.

For example Flask uses thread local objects internally so that you don't
have to pass objects around from function to function within a request in
order to stay threadsafe.  While this is a really easy approach and saves
you a lot of time, it also does not scale well to large applications.
It's especially painful for more complex unittests and when you suddenly
have to deal with code being executed outside of the context of a request
(for example if you have cronjobs).

Flask provides some tools to deal with the downsides of this approach but
the core problem of this approach obviously stays.  It is also based on
convention over configuration which means that a lot of things are
preconfigured in Flask and will work well for smaller applications but not
so much for larger ones (where and how it looks for templates, static
files etc.)

But don't worry if your application suddenly grows larger than it was
initially and you're afraid Flask might not grow with it.  Even with
larger frameworks you sooner or later will find out that you need
something the framework just cannot do for you without modification.
If you are ever in that situation, check out the :ref:`becomingbig`
chapter.

A Framework and An Example
--------------------------

Flask is not only a microframework, it is also an example.  Based on
Flask, there will be a series of blog posts that explain how to create a
framework.  Flask itself is just one way to implement a framework on top
of existing libraries.  Unlike many other microframeworks Flask does not
try to implement anything on its own, it reuses existing code.

Target Audience
---------------

Is Flask for you?  Is your application small-ish (less than 4000 lines of
Python code) and does not depend on too complex database structures, Flask
is the Framework for you.  It was designed from the ground up to be easy
to use, based on established principles, good intentions and on top of two
established libraries in widespread usage.

Flask serves two purposes: it's an example of how to create a minimal and
opinionated framework on top of Werkzeug to show how this can be done, and
to provide people with a simple tool to prototype larger applications or
to implement small and medium sized applications.

If you suddenly discover that your application grows larger than
originally intended, head over to the :ref:`becomingbig` section to see
some possible solutions for larger applications.

Satisfied?  Then head over to the :ref:`installation`.
