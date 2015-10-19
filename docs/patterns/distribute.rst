.. _distribute-deployment:

Deploying with Distribute
=========================

`Distribute`_ is a deprecated fork of the setuptools project. Since the
setuptools 0.7 release, Setuptools and Distribute have merged and Distribute
is no longer maintained. Please see `Setuptools`_ documentation for more
information.

Basic Setup Script
------------------

Because you have Flask running, you will have setuptools available on 
your system anyways.

If you do not, fear not, there is a script to install it for you:
`ez_setup.py`_.  Just download and run with your Python interpreter.

    $ python ez_setup.py

This will install a setuptools for your Python distribution.

Standard disclaimer applies: :ref:`you better use a virtualenv
<virtualenv>`.

Your setup code always goes into a file named :file:`setup.py` next to your
application. The name of the file is only convention, but because
everybody will look for a file with that name, you better not change it.

A basic :file:`setup.py` file for a Flask application looks like this::

    from setuptools import setup

    setup(
        name='Your Application',
        version='1.0',
        long_description=__doc__,
        packages=['yourapplication'],
        include_package_data=True,
        zip_safe=False,
        install_requires=['Flask']
    )

Please keep in mind that you have to list subpackages explicitly.  If you
want distribute to lookup the packages for you automatically, you can use
the `find_packages` function::

    from setuptools import setup, find_packages

    setup(
        ...
        packages=find_packages()
    )

Most parameters to the `setup` function should be self explanatory,
`include_package_data` and `zip_safe` might not be.
`include_package_data` tells distribute to look for a :file:`MANIFEST.in` file
and install all the entries that match as package data.  We will use this
to distribute the static files and templates along with the Python module
(see :ref:`distributing-resources`).  The `zip_safe` flag can be used to
force or prevent zip Archive creation.  In general you probably don't want
your packages to be installed as zip files because some tools do not
support them and they make debugging a lot harder.


.. _distributing-resources:

Distributing Resources
----------------------

If you try to install the package you just created, you will notice that
folders like :file:`static` or :file:`templates` are not installed for you.  The
reason for this is that distribute does not know which files to add for
you.  What you should do, is to create a :file:`MANIFEST.in` file next to your
:file:`setup.py` file.  This file lists all the files that should be added to
your tarball::

    recursive-include yourapplication/templates *
    recursive-include yourapplication/static *

Don't forget that even if you enlist them in your :file:`MANIFEST.in` file, they
won't be installed for you unless you set the `include_package_data`
parameter of the `setup` function to ``True``!


Declaring Dependencies
----------------------

Dependencies are declared in the `install_requires` parameter as list.
Each item in that list is the name of a package that should be pulled from
PyPI on installation.  By default it will always use the most recent
version, but you can also provide minimum and maximum version
requirements.  Here some examples::

    install_requires=[
        'Flask>=0.2',
        'SQLAlchemy>=0.6',
        'BrokenPackage>=0.7,<=1.0'
    ]

I mentioned earlier that dependencies are pulled from PyPI.  What if you
want to depend on a package that cannot be found on PyPI and won't be
because it is an internal package you don't want to share with anyone?
Just still do as if there was a PyPI entry for it and provide a list of
alternative locations where distribute should look for tarballs::

    dependency_links=['http://example.com/yourfiles']

Make sure that page has a directory listing and the links on the page are
pointing to the actual tarballs with their correct filenames as this is
how distribute will find the files.  If you have an internal company
server that contains the packages, provide the URL to that server there.


Installing / Developing
-----------------------

To install your application (ideally into a virtualenv) just run the
:file:`setup.py` script with the `install` parameter.  It will install your
application into the virtualenv's site-packages folder and also download
and install all dependencies::

    $ python setup.py install

If you are developing on the package and also want the requirements to be
installed, you can use the `develop` command instead::

    $ python setup.py develop

This has the advantage of just installing a link to the site-packages
folder instead of copying the data over.  You can then continue to work on
the code without having to run `install` again after each change.


.. _Distribute: https://pypi.python.org/pypi/distribute
.. _pip: https://pypi.python.org/pypi/pip
.. _ez_setup.py: http://peak.telecommunity.com/dist/ez_setup.py
.. _Setuptools: https://pythonhosted.org/setuptools
