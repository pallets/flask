.. _installation:

설치하기
============

Flask는 `Werkzeug
<http://werkzeug.pocoo.org/>`_ 와 `Jinja2 <http://jinja.pocoo.org/2/>`_ 
라이브러리에 의존적이다. Werkzeug는 웹어플리케이션과 다양한 서버 사이의 
개발과 배포를 위한 표준 파이썬 인터페이스인 WSGI를 구현한 툴킷이다.
Jinja2 는 HTML 템플릿을 렌더링 하는 템플릿엔진이다.

여러분은 어떻게 여러분의 컴퓨터에 Flaks와 관련된 모든 것들을 빠르게 
얻을 수 있을까? 선택할 수 있는 방법은 여러가지가 있으나 가장 강력한 
방법은 virtualenv을 사용하는 것이다. 그래서 먼저 virtualenv를 살펴보려 한다.

 
Flask 설치를 시작하기 위해 파이썬 2.5 또는 상위 버전을 사용할 것이다. 
그래서 최신 파이썬 2.x버전이 설치되어 있는 것을 확인해라. 
이 글을 쓰는 시점에 WSGI 명세서는 아직 파이썬 3을 위해 마무리되지 않았다. 
그래서 Flask는 파이썬 3.x 버전을 지원할 수 없다. 



.. _virtualenv:

virtualenv
----------

virtualenv는 아마도 당신이 개발 과정에서 꼭 사용해야만 하는 툴일것이다.
만약 당신이 운영서버에 쉘(shell) 환경에서 접속해야 하고 다양한 파이썬실행
환경이 필요하다면 유용하게 사용할 수 있는 툴이다.

virtualenv는 어떤 문제를 해결해 줄 수 있는가? 만약 당신이 나처럼 Python을
많이 사용하고 있고 Flask 기반의 웹 어플리케이션과 같이 현재 사용하고 있는
것과 다른 파이썬 환경을 사용해야 한다면 virtualenv를 사용해 볼 수 있는 좋은 
기회가 될 수 있다. 게다가 당신이 진행하고 있는 더 많은 프로젝트들이 서로 다른
Python 버전에서 작동해야 한다거나 혹은 서로 다른 버전의 Python 라이브러리들
에서 작동해야 한다면 어떨까? 현실을 직시해보자! 많은 라이브러리들은 종종 
하위버전 호환성들을 깨뜨린다. 그리고 어떤 심각한 응용프로그램이라 하더라도 
라이브러리와 의존관계가 없을 수는 없다. 그렇다면 두개 혹은 더 많은 당신의 
프로젝트들의 의존관계의 충돌을 해결하기 위해서 무엇을 할것인가?


Virtualenv가 당신을 구해 줄것이다. virtualenv를 이용하여 Python을 아무런 문제
없이 각각의 프로젝트 환경에 맞게 다중설치가 가능하도록 해준다. 이방법은 실제로 
독립된 버전의 Python 실행 환경에 단순히 복사하는 것이 아니라 서로 다른 프로젝트
환경이 독립적으로 실행 환경을 명백하게 가져갈 수 있도록 격리 시키는 방법이다.
이제 virtualenv가 어떻게 작동하는지 알아보자!



만약 당신이 Mac OS X 혹은 Linux 환경이라면, 다음의 두가지 명령어로 virtualenv를
작동시킬 수 있다::

    $ sudo easy_install virtualenv

혹은 좀더 나은 방법으로::

    $ sudo pip install virtualenv


위의 방법을 사용하면 당신의 시스템에 virtualenv가 설치 될걸이다. 아마도 당신의
시스템에서 사용하는 package manager를 사용할 수 도 있다. 
만약 당신이 우분투를 사용한다면 ::

    $ sudo apt-get install python-virtualenv

만약 당신이 Windows 를 사용하고 있거나 `easy_install` 명령어를 가지고 있지 않다면, 
명령어를 먼저 설치해야 한다.  :ref:`windows-easy-install` 을 확인하여 설치 방법에 대한 자세한 
정보를 확인할 수 있다. easy_install이 설치가 완료되면 위와 같은 방법으로 명령어를 실행하여
virtualenv를 설치할 수 있다. 다만, Windows 환경에서는 `sudo` 가 필요없다.



일단 virtualenv가 설치되었다면, 쉘을 실행시키고 자신만의 실행환경을 만들 수 있다.
나는 보통 프로젝트 폴더를 만들고 폴더안에서  `venv` 를 이용하여 다음과 같이 작업한다.
 ::

    $ mkdir myproject
    $ cd myproject
    $ virtualenv venv
    New python executable in venv/bin/python
    Installing distribute............done.


이제, 당신이 해당 프로젝트에서 작업하고 싶을 때마다, 그에 해당하는
실행환경을 활성화 시킬 수 있다. OS X혹은 Linux 환경이라면 다음과 같이
실행한다.::

    $ . venv/bin/activate

만약 당신이 Windows 사용자라면, 다음과 같이 실행한다.::

    $ venv\scripts\activate

어떤 방식이든, 당신은 이제 virtualenv 를 사용할 수밖에 없을 것이다.
(virtualenv이 활성화된 상태를 보여주기 위핸 당신의 쉘 프롬프트가 어떻게 변화 
되는지 주목하라).

이제 당신은 다음의 명령어를 입력하여 활성화된 virtualenv 를 통해 Flask를 
설치할 수 있다.::

    $ pip install Flask

몇초동안만 기다리면 설치가 완료 된다.


시스템 전체에 적용하여 설치
------------------------

이 방법이 가능하긴 하지만, 추천하지는 않겠다.
단지 루트(root)권한을 이용하여 `pip` 를 실행시키면 된다.::

    $ sudo pip install Flask

(Windows 시스템에서는 , 위 명령어를 명령어 프롬프트에서 관리자(administrator) 권한으로
실행시키면 된다. 그리고 `sudo` 는 생략하자.)


위태로운 모험 하기
------------------

만약 당신이 가장 최신버전의 Flask를 이용하여 작업을 하고 싶다면, 
두가지 방법이 있다.: `pip` 를 이용하여 작업환경으로 Flask의 개발중 버전을  가져오거나,
git checkout을 사용할 수 있다. 어떤 방법을 사용하든, virtualenv의 사용을 추천한다.

새로운 virtualenv를 만들고 git checkout을 실행하여 개발모드의 Flask를 실행할 수 있다.::

    $ git clone http://github.com/mitsuhiko/flask.git
    Initialized empty Git repository in ~/dev/flask/.git/
    $ cd flask
    $ virtualenv venv --distribute
    New python executable in venv/bin/python
    Installing distribute............done.
    $ . venv/bin/activate
    $ python setup.py develop
    ...
    Finished processing dependencies for Flask

이 방법을 통해 의존관계에 있는 것들을 가져오게 되고 git에 등록된 현재버전을
virtualenv안으로 가져오게 된다. 그다음에 ``git pull origin`` 을 통하여 최신
버전으로 업데이트가 가능하다. 

git을 사용하지 않고 최신 버전을 가져오는 방법은 다음과 같다.::

    $ mkdir flask
    $ cd flask
    $ virtualenv venv --distribute
    $ . venv/bin/activate
    New python executable in venv/bin/python
    Installing distribute............done.
    $ pip install Flask==dev
    ...
    Finished processing dependencies for Flask==dev

.. _windows-easy-install:


Windows에서의 `pip` 와 `distribute`
-----------------------------------

Windows 환경에서는 `easy_install` 의 설치가 조금 복잡해 보인다. 하지만 그래도 그리
어렵지 않다. 가장 쉬운 방법은 `distribute_setup.py`_ 를 다운로드 받아서 실행하는 것이다.
다운로드 폴더를 열고 다운 받은 파일을 더블클릭한다.

다음으로, `easy_install` 명령어를 `PATH` 에 실행경로로 추가하고 Python 설치 디렉토리의 
Scripts의 경로도 실행경로에 추가하여야 한다. 이렇게 하려면, 바탕화면이나 시작메뉴의 `내컴퓨터` 
아이콘을 마우스 오른쪽 버튼으로 클릭하여 나오는 메뉴에서 "등록정보"를 선택하여 실행한다.
이제 해당 메뉴에서 "고급 시스템 설정"(Windows XP의 경우 "고급" 탭) 을 선택한다.
다음으로 "환경 변수"를 선택한 후 "PATH" 를 클릭하여 "시스템 변수" 항목에 Python 설치 경로와
Python의 Scripts 폴더이름을 실행경로로 등록한다. 주의할 점은 기존에 설정되어 있는 값과
세미콜론(;)으로 구분되어져야 한다는 점이다. 설치된 Python 버전이 2.7이고 기본 경로에
설치되었다면 다음과 같을 것이다.::

    ;C:\Python27\Scripts

마침내 당신은 해냈다! 이제 제대로 동작하는지 확인해 보자, 명령어 창을 열고 프롬프트에 
``easy_install``. 만약 Windows Vista 혹은 Windows7 을 사용중이고 'User Account Control' 
이 활성화 되어 있다면 관리자 권한으로 진행하여야 한다.

이제 당신은 ``easy_install`` 를 손에 넣었다! ``pip`` 를 설치해 보자::

    > easy_install pip


.. _distribute_setup.py: http://python-distribute.org/distribute_setup.py
