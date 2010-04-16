.. _becomingbig:

Becoming Big
============

Your application is becoming more and more complex?  Flask is really not
designed for large scale applications and does not attempt to do so, but
that does not mean you picked the wrong tool in the first place.

Flask is powered by Werkzeug and Jinja2, two libraries that are in use at
a number of large websites out there and all Flask does is bringing those
two together.  Being a microframework, Flask is literally a single file.
What that means for large applications is that it's probably a good idea
to take the code from Flask and put it into a new module within the
applications and expanding on that.

What Could Be Improved?
-----------------------

For instance it makes a lot of sense to change the way endpoints (the
names of the functions / URL rules) are handled to also take the module
name into account.  Right now the function name is the URL name, but
imagine you have a large applications consisting of multiple components.
In that case, it makes a lot of sense to use dotted names for the URL
endpoints.

Here some suggestions how Flask can be modified to better accomodate large
scale applications:

-   implement dotted names for URL endpoints
-   get rid of the decorator function registering which causes a lot
    of troubles for applications that have circular dependencies.  It
    also requires that the whole application is imported when the system
    initializes or certain URLs will not be available right away.   A
    better solution would be to have one module with all URLs in there and
    specifing the target functions explicitly or by name and importing
    them when needed.
-   switch to explicit request object passing.  This makes it more to type
    (because you now have something to pass around) but it makes it a
    whole lot easier to debug hairy situations and to test the code.
-   integrate the `Babel`_ i18n package or `SQLAlchemy`_ directly into the
    core framework.

.. _Babel: http://babel.edgewall.org/
.. _SQLAlchemy: http://www.sqlalchemy.org/

Why does not Flask do all that by Default?
------------------------------------------

There is a huge difference between a small application that only has to
handle a couple of requests per second and with an overall code complexity
of less than 4000 lines of code or something of larger scale.  At one
point it becomes important to integrate external systems, different
storage backends and more.

If Flask was designed with all these contingencies in mind, it would be a
much more complex framework and less easy to get started with.
