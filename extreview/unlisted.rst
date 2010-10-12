Unlisted Extensions
===================

This is a list of extensions that is currently rejected from listing and
with that also not approved.  If an extension ends up here it should
improved to be listed.


Flask-Actions
-------------

:Last Review: 2010-07-25
:Reviewed Version: 0.2

Rejected because of missing description in PyPI, formatting issues with
the documentation (missing headlines, scrollbars etc.) and a general clash
of functionality with the Flask-Script package.  Latter should not be a
problem, but the documentation should improve.  For listing, the extension
developer should probably discuss the extension on the mailinglist with
others.

Futhermore it also has an egg registered with an invalid filename.


Flask-Jinja2Extender
--------------------

:Last Review: 2010-07-25
:Reviewed Version: 0.1

Usecase not obvious, hacky implementation, does not solve a problem that
could not be solved with Flask itself.  I suppose it is to aid other
extensions, but that should be discussed on the mailinglist.


Flask-Markdown
--------------

:Last Review: 2010-07-25
:Reviewed Version: 0.2

Would be great for enlisting but it should follow the API of Flask-Creole.
Besides that, the docstrings are not valid rst (run through rst2html to
see the issue) and it is missing tests.  Otherwise fine :)


flask-urls
----------

:Last Review: 2010-07-25
:Reviewed Version: 0.9.2

Broken PyPI index and non-conforming extension name.  Due to the small
featureset this was also delisted from the list.  It was there previously
before the approval process was introduced.
