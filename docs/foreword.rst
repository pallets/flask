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
it might be an issue for larger applications because in theory
modifications on these objects might happen anywhere in the same thread.

Flask is also based on convention over configuration, which means that
many things are preconfigured.  For example, by convention, templates and
static files are in subdirectories within the Python source tree of the
application.

The main reason however why Flask is called a "microframework" is the idea
to keep the core simple but extensible.  There is no database abstraction
layer, no form validation or anything else where different libraries
already exist that can handle that.  However Flask knows the concept of
extensions that can add this functionality into your application as if it
was implemented in Flask itself.  There are currently extensions for
object relational mappers, form validation, upload handling, various open
authentication technologies and more.

However Flask is not much code and it is built on a very solid foundation
and with that it is very easy to adapt for large applications.  If you are
interested in that, check out the :ref:`becomingbig` chapter.

If you are curious about the Flask design principles, head over to the
section about :ref:`design`.

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

The Status of Python 3
----------------------

Currently the Python community is in the process of improving libraries to
support the new iteration of the Python programming language.  While the
situation is greatly improving there are still some issues that make it
hard for us to switch over to Python 3 just now.  These problems are
partially caused by changes in the language that went unreviewed for too
long, partially also because we have not quite worked out how the lower
level API should change for the unicode differences in Python3.

Werkzeug and Flask will be ported to Python 3 as soon as a solution for
the changes is found, and we will provide helpful tips how to upgrade
existing applications to Python 3.  Until then, we strongly recommend
using Python 2.6 and 2.7 with activated Python 3 warnings during
development.  If you plan on upgrading to Python 3 in the near future we
strongly recommend that you read `How to write forwards compatible
Python code <http://lucumr.pocoo.org/2011/1/22/forwards-compatible-python/>`_.
