How to contribute to Flask
==========================

Thank you for considering contributing to Flask!

Support questions
-----------------

Please, don't use the issue tracker for this. Use one of the following
resources for questions about your own code:

* The ``#get-help`` channel on our Discord chat: https://discordapp.com/invite/t6rrQZH

  * The IRC channel ``#pocoo`` on FreeNode is linked to Discord, but
    Discord is preferred.

* The mailing list flask@python.org for long term discussion or larger issues.
* Ask on `Stack Overflow`_. Search with Google first using:
  ``site:stackoverflow.com flask {search term, exception message, etc.}``

.. _Stack Overflow: https://stackoverflow.com/questions/tagged/flask?sort=linked

Reporting issues
----------------

- Describe what you expected to happen.
- If possible, include a `minimal reproducible example`_ to help us
  identify the issue. This also helps check that the issue is not with
  your own code.
- Describe what actually happened. Include the full traceback if there was an
  exception.
- List your Python, Flask, and Werkzeug versions. If possible, check if this
  issue is already fixed in the repository.

.. _minimal reproducible example: https://stackoverflow.com/help/minimal-reproducible-example

Submitting patches
------------------

- Include tests if your patch is supposed to solve a bug, and explain
  clearly under which circumstances the bug happens. Make sure the test fails
  without your patch.
- Try to follow `PEP8`_, but you may ignore the line length limit if following
  it would make the code uglier.

First time setup
~~~~~~~~~~~~~~~~

- Download and install the `latest version of git`_.
- Configure git with your `username`_ and `email`_::

        git config --global user.name 'your name'
        git config --global user.email 'your email'

- Make sure you have a `GitHub account`_.
- Fork Flask to your GitHub account by clicking the `Fork`_ button.
- `Clone`_ your GitHub fork locally::

        git clone https://github.com/{username}/flask
        cd flask

- Add the main repository as a remote to update later::

        git remote add pallets https://github.com/pallets/flask
        git fetch pallets

- Create a virtualenv::

        python3 -m venv env
        . env/bin/activate
        # or "env\Scripts\activate" on Windows

- Install Flask in editable mode with development dependencies::

        pip install -e ".[dev]"

.. _GitHub account: https://github.com/join
.. _latest version of git: https://git-scm.com/downloads
.. _username: https://help.github.com/en/articles/setting-your-username-in-git
.. _email: https://help.github.com/en/articles/setting-your-commit-email-address-in-git
.. _Fork: https://github.com/pallets/flask/fork
.. _Clone: https://help.github.com/en/articles/fork-a-repo#step-2-create-a-local-clone-of-your-fork

Start coding
~~~~~~~~~~~~

-   Create a branch to identify the issue you would like to work on. If
    you're submitting a bug or documentation fix, branch off of the
    latest ".x" branch::

        git checkout -b your-branch-name origin/1.0.x

    If you're submitting a feature addition or change, branch off of the
    "master" branch::

        git checkout -b your-branch-name origin/master

- Using your favorite editor, make your changes, `committing as you go`_.
- Try to follow `PEP8`_. We have a pre-commit config and tests that will
  ensure the code follows our style guide.
- Include tests that cover any code changes you make. Make sure the test fails
  without your patch. `Run the tests. <contributing-testsuite_>`_.
- Push your commits to GitHub and `create a pull request`_ by using::

        git push --set-upstream origin your-branch-name

- Celebrate 🎉

.. _committing as you go: https://dont-be-afraid-to-commit.readthedocs.io/en/latest/git/commandlinegit.html#commit-your-changes
.. _PEP8: https://pep8.org/
.. _create a pull request: https://help.github.com/en/articles/creating-a-pull-request

.. _contributing-testsuite:

Running the tests
~~~~~~~~~~~~~~~~~

Run the basic test suite with::

    pytest

This only runs the tests for the current environment. Whether this is relevant
depends on which part of Flask you're working on. Travis-CI will run the full
suite when you submit your pull request.

The full test suite takes a long time to run because it tests multiple
combinations of Python and dependencies. You need to have Python 2.7, 3.4,
3.5 3.6, and PyPy 2.7 installed to run all of the environments. Then run::

    tox

Running test coverage
~~~~~~~~~~~~~~~~~~~~~

Generating a report of lines that do not have test coverage can indicate
where to start contributing. Run ``pytest`` using ``coverage`` and generate a
report on the terminal and as an interactive HTML document::

    coverage run -m pytest
    coverage report
    coverage html
    # then open htmlcov/index.html

Read more about `coverage <https://coverage.readthedocs.io>`_.

Running the full test suite with ``tox`` will combine the coverage reports
from all runs.


Building the docs
~~~~~~~~~~~~~~~~~

Build the docs in the ``docs`` directory using Sphinx::

    cd docs
    make html

Open ``_build/html/index.html`` in your browser to view the docs.

Read more about `Sphinx <https://www.sphinx-doc.org/en/master/>`_.


Caution: zero-padded file modes
-------------------------------

This repository contains several zero-padded file modes that may cause issues
when pushing this repository to git hosts other than GitHub. Fixing this is
destructive to the commit history, so we suggest ignoring these warnings. If it
fails to push and you're using a self-hosted git service like GitLab, you can
turn off repository checks in the admin panel.

These files can also cause issues while cloning. If you have ::

    [fetch]
    fsckobjects = true

or ::

    [receive]
    fsckObjects = true

set in your git configuration file, cloning this repository will fail. The only
solution is to set both of the above settings to false while cloning, and then
setting them back to true after the cloning is finished.
