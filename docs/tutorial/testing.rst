.. _tutorial-testing:

Bonus: Testing the Application
==============================

Now that you have finished the application and everything works as
expected, it's probably not a bad idea to add automated tests to simplify
modifications in the future.  The application above is used as a basic
example of how to perform unit testing in the :ref:`testing` section of the
documentation.  Go there to see how easy it is to test Flask applications.

Adding Tests to flaskr
======================

Assuming you have seen the testing section above and have either written
your own tests for ``flaskr`` or have followed along with the examples
provided, you might be wondering about ways to organize the project.

One possible and recommended project structure is::

    flaskr/
        flaskr/
            __init__.py
            static/
            templates/
        tests/
            context.py
            test_flaskr.py
        setup.py
        MANIFEST.in

For now go ahead a create the :file:`tests/` directory as well as the
:file:`context.py` and :file:`test_flaskr.py` files, if you haven't
already. The context file is used as an import helper. The contents
of that file are::

    import sys, os

    basedir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, basedir + '/../')

    from flaskr import flaskr

Testing + Setuptools
====================

One way to handle testing is to integrate it with ``setuptools``. All it
requires is adding a couple of lines to the :file:`setup.py` file and
creating a new file :file:`setup.cfg`. Go ahead and update the
:file:`setup.py` to contain::

    from setuptools import setup

    setup(
        name='flaskr',
        packages=['flaskr'],
        include_package_data=True,
        install_requires=[
            'flask',
        ],
    )
        setup_requires=[
            'pytest-runner',
        ],
        tests_require=[
            'pytest',
        ],
    )
Now create :file:`setup.cfg` in the project root (alongside
:file:`setup.py`)::

    [aliases]
    test=pytest

Now you can run::

    python setup.py test

This calls on the alias created in :file:`setup.cfg` which in turn runs
``pytest`` via ``pytest-runner``, as the :file:`setup.py` script has
been called. (Recall the `setup_requires` argument in :file:`setup.py`)
Following the standard rules of test-discovery your tests will be
found, run, and hopefully pass.

This is one possible way to run and manage testing.  Here ``pytest`` is
used, but there are other options such as ``nose``.  Integrating testing
with ``setuptools`` is convenient because it is not necessary to actually
download ``pytest`` or any other testing framework one might use.