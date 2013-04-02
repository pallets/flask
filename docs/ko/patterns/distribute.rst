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
   "진입점(entry point)"을 선언할 수 있도록 하는 진입점을 지원하다는 것이다.
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

표준적인 포기는 다음을 적용한다. :ref:`여러분은 virtualenv를 사용하는 것이 낫다.<virtualenv>`.

여러분의 셋업 코드는 항상 `setup.py`이라는 파일명으로 여러분의 어플리케이션 옆에 놓인다.
그 파일명은 단지 관례일뿐이지만, 모두가 그 이름으로 파일을 찾을 것이기 때문에
다른 이름으로 바꾸지 않는게 좋을 것이다.

그렇다, 여러분은 `distribute`를 사용하고 있음에도 불구하고, 
`setuptools`라 불리는 패키지를 입포트하고 있다.  `distribute` 은 `setuptools` 과 완전하게 하위버전이 
호환되므로 임포트 명을 또한 사용한다.

플라스크 어플리케이션에 대한 기본적인 `setup.py` 파일은 아래와 같다::

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

여러분은 명시적으로 하위 패키지들을 나열해야만 한다는 것을 명심해야한다.
여러분이 자동적으로 distribute가 패키지명을 찾아보기를 원한다면,
`find_packages` 함수를 사용할 수 있다::

    from setuptools import setup, find_packages

    setup(
        ...
        packages=find_packages()
    )

`include_package_data` 과 `zip_safe` 은 아닐수도 있지만, `setup` 함수의
대부분 인자들은 스스로 설명이 가능해야 한다. 
`include_package_data` 은 distribute 에게 `MANIFEST.in` 파일을 찾고 
패키지 데이타로서 일치하는 모든 항목을 설치하도록 요청한다.
우리들은 파이썬 모듈과 같이 정적 파일들과 템플릿들을 배포하기 위해 
이것을 사용할 것이다.(see :ref:`distributing-resources`).
`zip_safe` 플래그는 zip 아카이브의 생성을 강제하거나 막기위해 사용될 수 있다.
일반적으로 여러분은 아마 여러분의 패키지들이 zip 파일로 설치되기를 원하지는 않을 것인데,
왜냐하면 어떤 도구들은 그것들을 지원하지 않으며 디버깅을 훨씬 더 어렵게 한다.


.. _distributing-resources:

리소스 배포하기
---------------

여러분이 방금 생성한 패키지를 설치하려고 한다면, 여러분은 `static` 이나
'templates' 같은 폴더들이 생성되어 있지 않다는 것을 알게될 것이다.
왜냐하면 distribute 은 추가할 파일이 어떤 것인지 모르기 때문이다.
여러분이 해야하는 것은 `setup.py' 파일 옆에 `MANIFEST.in` 파일을 생성하는 것이다.
이 파일은 여러분의 타르볼(tarball)에 추가되어야 하는 모든 파일들을 나열한다::

    recursive-include yourapplication/templates *
    recursive-include yourapplication/static *

여러분이 `MANIFEST.in` 파일에 그 목록들을 요청함에도 불구하고, `setup` 함수의 
`include_package_data` 인자가 `True` 로 설정되지 않는다면, 그것들은 설치되지 
않을 것이라는 것을 잊지 말도록 해라.


의존성 선언하기
---------------

의존성은 `install_requires` 인자에 리스트로 선언된다. 그 리스트에 있는 각 항목은
설치 시 PyPI로 부터 당겨져야 하는 패키지 명이다. 디폴트로 항상 최신 버전을 사용하지만, 
여러분은 또한 최소 버전과 최대 버전에 대한 요구사항을 제공할 수 있다. 아래에 예가 있다::

    install_requires=[
        'Flask>=0.2',
        'SQLAlchemy>=0.6',
        'BrokenPackage>=0.7,<=1.0'
    ]

앞에서 의존성은 PyPI로부터 당겨진다고 언급했다. 다른 사람과 공유하고
싶지 않은 내부 패키지기 때문에 PyPI에서 찾을 수 없고 찾지 못하는 
패키지에 의존하고 싶다면 어떻게 되는가? Just still do as if there was a PyPI entry for it and provide a list of
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
