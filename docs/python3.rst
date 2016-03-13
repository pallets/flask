.. _python3-support:

Python 3 Support
================

Flask and all of its dependencies support Python 3 so you can in theory
start working on it already.  There are however a few things you should be
aware of before you start using Python 3 for your next project.

If you want to use Flask with Python 3 you will need to use Python 3.3 or
higher.  3.2 and older are *not* supported.

In addition to that you need to use the latest and greatest versions of
`itsdangerous`, `Jinja2` and `Werkzeug`. Flask 0.10 and Werkzeug 0.9 were
the first versions to introduce Python 3 support.

Some of the decisions made in regards to unicode and byte utilization on
Python 3 make it hard to write low level code.  This mainly affects WSGI
middlewares and interacting with the WSGI provided information.  Werkzeug
wraps all that information in high-level helpers but some of those were
specifically added for the Python 3 support and are quite new.

Unless you require absolute compatibility, you should be fine with Python 3
nowadays. Most libraries and Flask extensions have been ported by now and
using Flask with Python 3 is generally a smooth ride. However, keep in mind
that most libraries (including Werkzeug and Flask) might not quite as stable
on Python 3 yet. You might therefore sometimes run into bugs that are
usually encoding-related.

The majority of the upgrade pain is in the lower-level libraries like
Flask and Werkzeug and not in the actual high-level application code.  For
instance all of the Flask examples that are in the Flask repository work
out of the box on both 2.x and 3.x and did not require a single line of
code changed.
