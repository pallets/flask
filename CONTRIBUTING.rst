==========================
How to contribute to Flask
==========================

Thanks for considering contributing to Flask.

Support questions
=================

Please, don't use the issue tracker for this. Check whether the ``#pocoo`` IRC
channel on Freenode can help with your issue. If your problem is not strictly
Werkzeug or Flask specific, ``#python`` is generally more active.
`Stack Overflow <https://stackoverflow.com/>`_ is also worth considering.

Reporting issues
================

- Under which versions of Python does this happen? This is even more important
  if your issue is encoding related.

- Under which versions of Werkzeug does this happen? Check if this issue is
  fixed in the repository.

Submitting patches
==================

First time setup
----------------

- Download and install the `latest version of git`_.
- Configure git with your `username`_ and `email`_.
- Make sure you have a `GitHub account`_.
- Fork Flask to your GitHub account by clicking the `Fork`_ button.
- `Clone`_ your GitHub fork locally.
- Add the main repository as a remote to update later.
  ``git remote add pallets https://github.com/pallets/flask``

.. _GitHub account: https://github.com/join
.. _latest version of git: https://git-scm.com/downloads
.. _username: https://help.github.com/articles/setting-your-username-in-git/
.. _email: https://help.github.com/articles/setting-your-email-in-git/
.. _Fork: https://github.com/pallets/flask/pull/2305#fork-destination-box
.. _Clone: https://help.github.com/articles/fork-a-repo/#step-2-create-a-local-clone-of-your-fork

Start coding
------------

- Create a branch to identify the issue you would like to work on (e.g.
  ``2287-dry-test-suite``)
- Using your favorite editor, make your changes, `committing as you go`_.
- Try to follow `PEP8`_, but you may ignore the line length limit if following
  it would make the code uglier.
- Include tests that cover any code changes you make. Make sure the test fails
  without your patch. `Run the tests. <contributing-testsuite_>`_.
- Push your commits to GitHub and `create a pull request`_.
- Celebrate 🎉

.. _committing as you go: http://dont-be-afraid-to-commit.readthedocs.io/en/latest/git/commandlinegit.html#commit-your-changes
.. _PEP8: https://pep8.org/
.. _create a pull request: https://help.github.com/articles/creating-a-pull-request/

.. _contributing-testsuite:

Running the testsuite
---------------------

You probably want to set up a `virtualenv
<https://virtualenv.readthedocs.io/en/latest/index.html>`_.

The minimal requirement for running the testsuite is ``pytest``.  You can
install it with::

    pip install pytest

Clone this repository::

    git clone https://github.com/pallets/flask.git

Install Flask as an editable package using the current source::

    cd flask
    pip install --editable .

Then you can run the testsuite with::

    pytest tests/

With only pytest installed, a large part of the testsuite will get skipped
though.  Whether this is relevant depends on which part of Flask you're working
on.  Travis is set up to run the full testsuite when you submit your pull
request anyways.

If you really want to test everything, you will have to install ``tox`` instead
of ``pytest``. You can install it with::

    pip install tox

The ``tox`` command will then run all tests against multiple combinations
Python versions and dependency versions.

Running test coverage
---------------------
Generating a report of lines that do not have unit test coverage can indicate where
to start contributing.  ``pytest`` integrates with ``coverage.py``, using the ``pytest-cov``
plugin.  This assumes you have already run the testsuite (see previous section)::

    pip install pytest-cov

After this has been installed, you can output a report to the command line using this command::

    pytest --cov=flask tests/

Generate a HTML report can be done using this command::

    pytest --cov-report html --cov=flask tests/

Full docs on ``coverage.py`` are here: https://coverage.readthedocs.io

Caution
=======
pushing
-------
This repository contains several zero-padded file modes that may cause issues when pushing this repository to git hosts other than github. Fixing this is destructive to the commit history, so we suggest ignoring these warnings. If it fails to push and you're using a self-hosted git service like Gitlab, you can turn off repository checks in the admin panel.


cloning
-------
The zero-padded file modes files above can cause issues while cloning, too. If you have

::

    [fetch]
    fsckobjects = true

or

::

    [receive]
    fsckObjects = true


set in your git configuration file, cloning this repository will fail. The only solution is to set both of the above settings to false while cloning, and then setting them back to true after the cloning is finished.
