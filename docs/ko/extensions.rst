Flask 확장기능
================
Flask 확장기능(extensions)은 서로 다른 다양한 방법으로 Flask 의 기능을 추가 시킬 수 있게 해준다.
예를 들어 확장기능을 이용하여 데이터베이스 그리고 다른 일반적인 태스크들을 지원할 수 있다.


확장기능 찾아내기
------------------

플라스크 확장기능들의 목록은 `Flask Extension Registry`_ 에서 살펴볼 수 있다. 
그리고 ``easy_install`` 혹은 ``pip`` 를 통해 다운로드 할 수 있다. 
만약 여러분이 Flask 확장기능을 추가하면,  ``requirements.rst`` 혹은 ``setup.py`` 에 명시된
파일 의존관계로부터 간단한 명령어의 실행이나 응용 프로그램 설치와 함께 설치될 수 있다.


확장기능 사용하기
----------------

확장기능은 일반적으로 해당 기능을 사용하는 방법을 보여주는 문서를 가지고 있다.
이 확장기능의 작동 방식에 대한 일반적인 규칙은 없지만, 확장기능은 공통된 위치에서 
가져오게 된다. 만약 여러분이 ``Flask-Foo`` 혹은 ``Foo-Flask`` 라는 확장기능을 
호출 하였다면, 그것은 항상 ``flask.ext.foo`` 을 통해서 가져오게 될 것이다 ::

    from flask.ext import foo


Flask 0.8 이전버전의 경우
----------------


만약 여러분의 Flask가 0.7 버전 혹은 그 이전의 것이라면 :data:`flask.ext` 패키지가
존재하지 않는다. 대신에 여러분은 ``flaskext.foo`` 혹은 ``flask_foo`` 등의 형식으로
확장기능이 배포되는 방식에 따라 불러와야만 한다. 만약 여러분이 여전히 Flask 0.7 혹은 이전
이전 버전을 지원하는 어플리케이션을 개발하기 원한다면, 여러분은 여전히  :data:`flask.ext` 
패키지를 불러와야만 한다. 우리는 Flask 의 이전 버전의 Flask를 위한 호환성 모듈을 제공하고 있다.
여러분은 github을 통해서 : `flaskext_compat.py`_ 를 다운로드 받을 수 있다. 

그리고 여기에서 호환성 모듈의 사용 방법을 볼 수 있다::


    import flaskext_compat
    flaskext_compat.activate()

    from flask.ext import foo



``flaskext_compat`` 모듈이 활성화 되면  :data:`flask.ext` 가 존재하게 되고 
여러분은 이것을 통해 여기서부터 불러오기를 시작 할 수 있다.


.. _Flask Extension Registry: http://flask.pocoo.org/extensions/
.. _flaskext_compat.py: https://github.com/mitsuhiko/flask/raw/master/scripts/flaskext_compat.py
