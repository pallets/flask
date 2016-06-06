.. _python3-support:

Python 3 Support
================

Flask, its dependencies, and most Flask extensions support Python 3.
You should start using Python 3 for your next project,
but there are a few things to be aware of.

You need to use Python 3.3 or higher.  3.2 and older are *not* supported.

You should use the latest versions of all Flask-related packages.
Flask 0.10 and Werkzeug 0.9 were the first versions to introduce Python 3 support.

Python 3 changed how unicode and bytes are handled, which complicates how low
level code handles HTTP data.  This mainly affects WSGI middleware interacting
with the WSGI ``environ`` data.  Werkzeug wraps that information in high-level
helpers, so encoding issues should not affect you.

The majority of the upgrade work is in the lower-level libraries like
Flask and Werkzeug, not the high-level application code.
For example, all of the examples in the Flask repository work on both Python 2 and 3
and did not require a single line of code changed.
