.. _tutorial-testing:

Bonus: Testing the Application
==============================

Now that you have finished the application and everything works as
expected, it's a good idea to add automated tests to simplify
modifications in the future.  The application above is used as a basic
example of how to perform unit testing in the :ref:`testing` section of the
documentation.  Go there to see how to test Flask applications.

Adding Tests to flaskr
======================

You might be wondering about ways to organize the project to include 
tests. One possible project structure is::

    flaskr/
        flaskr/
            __init__.py
            static/
            templates/
        tests/
            test_flaskr.py
        setup.py
        MANIFEST.in

For now go ahead a create the :file:`tests/` directory and 
:file:`test_flaskr.py`. If you unsure of what to add in order to 
start testing the application, take a look here: :ref:`testing`. 

Running the Tests
=================

At this point you can run the tests. Here ``pytest`` will be 
used. Here are the commands to do that. This code example is 
run within the top-level :file:`flaskr/` directory)::

    pip install --editable . 
    pip install pytest
    py.test

At this point you can run the tests and they should all pass. This
application structure follows ``pytests`` "good integration practices".
It's worth taking a look at. Note: These tests passing require that 
your application be installed in the same virtualenv as pytest. Otherwise
the import statement `from flaskr import flaskr`, in 
:file:`test_flaskr.py` will fail.

Testing + Setuptools
====================

One way to handle testing is to integrate it with ``setuptools``. Here 
that requires is adding a couple of lines to the :file:`setup.py` file 
and creating a new file :file:`setup.cfg`. Go ahead and update the
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

Now you can run the tests with (within top-level :file:`flaskr` 
directory)::

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
