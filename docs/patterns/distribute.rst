.. _distribute-deployment:

Deploying with Distribute
=========================

`distribute`_, formerly setuptools, is an extension library that is
commonly used to (like the name says) distribute Python libraries and
extensions.  It extends distutils, a basic module installation system
shipped with Python to also support various more complex constructs that
make larger applications easier to distribute:

- **support for dependencies**: a library or application can declare a
  list of other libraries it depends on which will be installed
  automatically for you.
- **package registry**: setuptools registers your package with your
  Python installation.  This makes it possible to query information
  provided by one package from another package.  The best known feature of
  this system is the entry point support which allows one package to
  declare an "entry point" another package can hook into to extend the
  other package.
- **installation manager**: `easy_install`, which comes with distribute
  can install other libraries for you.  You can also use `pip`_ which
  sooner or later will replace `easy_install` which does more than just
  installing packages for you.

Flask itself, and all the libraries you can find on the cheeseshop
are distributed with either distribute, the older setuptools or distutils.

In this case we assume your application is called
`yourapplication.py` and you are not using a module, but a :ref:`package
<larger-applications>`.  Distributing resources with standard modules is
not supported by `distribute`_ so we will not bother with it.  If you have
not yet converted your application into a package, head over to the
:ref:`larger-applications` pattern to see how this can be done.

A working deployment with distribute is the first step into more complex
and more automated deployment scenarios.  If you want to fully automate
the process, also read the :ref:`fabric-deployment` chapter.

Basic Setup Script
------------------

Because you have Flask running, you either have setuptools or distribute
available on your system anyways.  If you do not, fear not, there is a
script to install it for you: `distribute_setup.py`_.  Just download and
run with your Python interpreter.

Standard disclaimer applies: :ref:`you better use a virtualenv
<virtualenv>`.

Your setup code always goes into a file named `setup.py` next to your
application.  The name of the file is only convention, but because
everybody will look for a file with that name, you better not change it.

Yes, even if you are using `distribute`, you are importing from a package
called `setuptools`.  `distribute` is fully backwards compatible with
`setuptools`, so it also uses the same import name.

A basic `setup.py` file for a Flask application looks like this::

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
`include_package_data` tells distribute to look for a `MANIFEST.in` file
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
folders like `static` or `templates` are not installed for you.  The
reason for this is that distribute does not know which files to add for
you.  What you should do, is to create a `MANIFEST.in` file next to your
`setup.py` file.  This file lists all the files that should be added to
your tarball::

    recursive-include yourapplication/templates *
    recursive-include yourapplication/static *

Don't forget that even if you enlist them in your `MANIFEST.in` file, they
won't be installed for you unless you set the `include_package_data`
parameter of the `setup` function to `True`!


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
`setup.py` script with the `install` parameter.  It will install your
application into the virtualenv's site-packages folder and also download
and install all dependencies::

    $ python setup.py install

If you are developing on the package and also want the requirements to be
installed, you can use the `develop` command instead::

    $ python setup.py develop

This has the advantage of just installing a link to the site-packages
folder instead of copying the data over.  You can then continue to work on
the code without having to run `install` again after each change.


.. _distribute: http://pypi.python.org/pypi/distribute
.. _pip: http://pypi.python.org/pypi/pip
.. _distribute_setup.py: http://python-distribute.org/distribute_setup.py
