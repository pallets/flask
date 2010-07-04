.. _becomingbig:

Becoming Big
============

Your application is becoming more and more complex?  If you suddenly
realize that Flask does things in a way that does not work out for your
application there are ways to deal with that.

Flask is powered by Werkzeug and Jinja2, two libraries that are in use at
a number of large websites out there and all Flask does is bring those
two together.  Being a microframework Flask does not do much more than
combinding existing libraries - there is not a lot of code involved.
What that means for large applications is that it's very easy to take the
code from Flask and put it into a new module within the applications and
expand on that.

Flask is designed to be extended and modified in a couple of different
ways:

-   Subclassing.  The majority of functionality can be changed by creating
    a new subclass of the :class:`~flask.Flask` class and overriding
    some methods.

-   Flask extensions.  For a lot of reusable functionality you can create
    extensions.

-   Forking.  If nothing else works out you can just take the Flask
    codebase at a given point and copy/paste it into your application
    and change it.  Flask is designed with that in mind and makes this
    incredible easy.  You just have to take the package and copy it
    into your application's code and rename it (for example to
    `framework`).  Then you can start modifying the code in there.

Why consider Forking?
---------------------

The majority of code of Flask is within Werkzeug and Jinja2.  These
libraries do the majority of the work.  Flask is just the paste that glues
those together.  For every project there is the point where the underlying
framework gets in the way (due to assumptions the original developers
had).  This is natural because if this would not be the case, the
framework would be a very complex system to begin with which causes a
steep learning curve and a lot of user frustration.

This is not unique to Flask.  Many people use patched and modified
versions of their framework to counter shortcomings.  This idea is also
reflected in the license of Flask.  You don't have to contribute any
changes back if you decide to modify the framework.

The downside of forking is of course that Flask extensions will most
likely break because the new framework has a different import name and
because of that forking should be the last resort.

Scaling like a Pro
------------------

For many web applications the complexity of the code is less an issue than
the scaling for the number of users or data entries expected.  Flask by
itself is only limited in terms of scaling by your application code, the
data store you want to use and the Python implementation and webserver you
are running on.

Scaling well means for example that if you double the amount of servers
you get about twice the performance.  Scaling bad means that if you add a
new server the application won't perform any better or would not even
support a second server.

There is only one limiting factor regarding scaling in Flask which are
the context local proxies.  They depend on context which in Flask is
defined as being either a thread or a greenlet.  Separate processes are
fine as well.  If your server uses some kind of concurrency that is not
based on threads or greenlets, Flask will no longer be able to support
these global proxies.  However the majority of servers are using either
threads, greenlets or separate processes to achieve concurrency which are
all methods well supported by the underlying Werkzeug library.
