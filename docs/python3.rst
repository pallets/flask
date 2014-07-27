.. _python3-support:

Python 3 Support
================

Flask and all of its dependencies support Python 3 so you can in theory
start working on it already.  There are however a few things you should be
aware of before you start using Python 3 for your next project.

Requirements
------------

If you want to use Flask with Python 3 you will need to use Python 3.3 or
higher.  3.2 and older are *not* supported.

In addition to that you need to use the latest and greatest versions of
`itsdangerous`, `Jinja2` and `Werkzeug`.

API Stability
-------------

Some of the decisions made in regards to unicode and byte utilization on
Python 3 make it hard to write low level code.  This mainly affects WSGI
middlewares and interacting with the WSGI provided information.  Werkzeug
wraps all that information in high-level helpers but some of those were
specifically added for the Python 3 support and are quite new.

A lot of the documentation out there on using WSGI leaves out those
details as it was written before WSGI was updated to Python 3.  While the
API for Werkzeug and Flask on Python 2.x should not change much we cannot
guarantee that this won't happen on Python 3.

Few Users
---------

Although moving to Python 3 should be done someday, most people still use
Python 2 for now.  As a result many of the problems you will encounter are
probably hard to search for on the internet if they are Python 3 specific.

Small Ecosystem
---------------

Some Flask extensions, documentation and PyPI provided libraries do not
support Python 3 yet.

Even if you start your project with knowing that all you will need is
supported by Python 3 you don't know what happens six months from now.
But if you are familiar with Python 3 and Flask extension, you can start
porting libraries on your own.

Recommendations
---------------

Unless you are already familiar with the differences in the versions we
recommend sticking to current versions of Python until the ecosystem
caught up.

The majority of the upgrade pain is in the lower-level libararies like
Flask and Werkzeug and not in the actual high-level application code.  For
instance all of the Flask examples that are in the Flask repository work
out of the box on both 2.x and 3.x and did not require a single line of
code changed.
