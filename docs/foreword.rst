Foreword
========

Read this before you get started with Flask.  This hopefully answers some
questions about the purpose and goals of the project, and when you
should or should not be using it.

What does "micro" mean?
-----------------------

To me, the "micro" in microframework refers not only to the simplicity and
small size of the framework, but also to the typically limited complexity
and size of applications that are written with the framework.  Also the
fact that you can have an entire application in a single Python file.  To
be approachable and concise, a microframework sacrifices a few features
that may be necessary in larger or more complex applications.

For example, Flask uses thread-local objects internally so that you don't
have to pass objects around from function to function within a request in
order to stay threadsafe.  While this is a really easy approach and saves
you a lot of time, it might also cause some troubles for very large
applications because changes on these thread-local objects can happen
anywhere in the same thread.

Flask provides some tools to deal with the downsides of this approach but
it might be an issue for larger applications.  Flask is also based on
convention over configuration, which means that many things are
preconfigured and will work well for smaller applications but not so well
for larger ones.  For example, by convention, templates and static files
are in subdirectories within the Python source tree of the application.

However Flask is not much code and built in a very solid foundation and
with that very easy to adapt for large applications.  If you are
interested in that, check out the :ref:`becomingbig` chapter.

A Framework and an Example
--------------------------

Flask is not only a microframework; it is also an example.  Based on
Flask, there will be a series of blog posts that explain how to create a
framework.  Flask itself is just one way to implement a framework on top
of existing libraries.  Unlike many other microframeworks, Flask does not
try to implement everything on its own; it reuses existing code.

Web Development is Dangerous
----------------------------

I'm not joking.  Well, maybe a little.  If you write a web
application, you are probably allowing users to register and leave their
data on your server.  The users are entrusting you with data.  And even if
you are the only user that might leave data in your application, you still
want that data to be stored securely.

Unfortunately, there are many ways the security of a web application can be
compromised.  Flask protects you against one of the most common security
problems of modern web applications: cross-site scripting (XSS).  Unless
you deliberately mark insecure HTML as secure, Flask and the underlying
Jinja2 template engine have you covered.  But there are many more ways to
cause security problems.

The documentation will warn you about aspects of web development that
require attention to security.  Some of these security concerns
are far more complex than one might think, and we all sometimes underestimate
the likelihood that a vulnerability will be exploited, until a clever
attacker figures out a way to exploit our applications.  And don't think
that your application is not important enough to attract an attacker.
Depending on the kind of attack, chances are that automated bots are
probing for ways to fill your database with spam, links to malicious
software, and the like.

So always keep security in mind when doing web development.

Target Audience
---------------

Is Flask for you?  If your application is small or medium sized and does
not depend on very complex database structures, Flask is the Framework for
you.  It was designed from the ground up to be easy to use, and built on
the firm foundation of established principles, good intentions, and
mature, widely used libraries.  Recent versions of Flask scale nicely
within reasonable bounds, and if you grow larger, you won't have any
trouble adjusting Flask for your new application size.

If you suddenly discover that your application grows larger than
originally intended, head over to the :ref:`becomingbig` section to see
some possible solutions for larger applications.

Satisfied?  Then let's proceed with :ref:`installation`.
