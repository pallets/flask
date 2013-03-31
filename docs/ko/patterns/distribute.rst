.. _distribute-deployment:

Distribute으로 전개하기
=========================

예전에 설치툴(setuptool)이었던 `distribute`_ 가 지금은 파이썬 라이브러리와 
확장(extentions)을 배포(툴의 이름처럼)하는데 일반적으로 사용되는 확장 라이브러리이다. 
그것은 더 규모있는 어플리케이션의 배포를 쉽게 만드는 여러 더 복잡한 생성자 또한 
지원하기 위해 파이썬과 같이 설치되는 disutils를 확장한 것이다::

- **의존성 지원(support for dependencies)**: 라이브러리나 어플리케이션은 여러분을 위해 자동으로 설치되어야 할
  그것에 의존적인 다른 라이브러리들의 목록을 선언할 수 있다.
- **패키지 레지스트리(package registry)**: 설치툴은 파이썬 설치와 함께 여러분의 패키지를 등록한다.
  이것은 하나의 패키지에서 제공되는 정보를 다른 패키지에서 질의하는 것을 가능하게 한다.
  이 시스템의 가장 잘 알려진 특징은 패키지가 다른 패키지를 확장하기 위해 끼어들 수 있는 
   "진입점(entry point")을 선언할 수 있도록 하는 진입점을 지원하다는 것이다.
- **설치 관리자(installation manager)**: distribute와 함께 설치되는 `easy_install` 은 여러분을 위해
  다른 라이브러리를 설치해준다.  여러분은 또한 조만간 패키지 설치 이상의 기능을 제공하는 `easy_install`
  을 대체할 `pip`_ 을 사용할 수 있다.

플라스크 그 자체와 cheeseshop(파이썬 라이브러리 인덱스)에서 찾을 수 있는 모든 라이브러리들은
distribute, the older setuptools 또는 distutils 중 한 가지로 배포된다.

이 경우, 여러분은 여러분의 어플리케이션이 `yourapplication.py` 이고 모듈을 사용하지 않지만
:ref:`package<larger-applications>` 를 사용한다고 가정하자.
표준 모듈들을 가진 리소스들을 배포하는 것은 `distribute`_ 이 지원하지 않지만,
우리는 그것을 신경쓰지 않을 것이다.  여러분이 아직 어플리케이션을 패키지로 변환하지 않았다면,
어떻게 변환될 수 있는지 보기 위해 :ref:`larger-applications` 패턴으로 돌아가길 바란다.

distribute를 가지고 배포하는 것은 좀 더 복잡하고 자동화된 배포 시나리오로 들어가는 첫 단계이다.
만약 여러분이 배포 프로세스를 완전히 자동화하고 싶다면, :ref:`fabric-deployment` 장 또한 읽어야한다.

기본 설치 스크립트
------------------

여러분은 플라스크를 실행시키고 있기 때문에, 어쨌든 여러분의 시스템에는
setuptools나 distribute를 사용할 수 있을 것이다. 
만약 사용할 수 없다면, 두려워하지 말기 바란다. 여러분을 위해 그런 설치도구를 설치해 줄 
`distribute_setup.py`_ 이라는 스크립트가 있다.  단지 다운받아서 파이썬으로 실행하면 된다.

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
