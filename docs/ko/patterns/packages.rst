.. _larger-applications:

더 큰 어플케이션들
===================

더 큰 어플리케이션들의 경우, 모듈 대신 패키지를 사용하는게 좋다.패키지의 사용은 꽤 간단하다.작은 어플리케이션은 아래와 같은 구조로 되어있다고 생각해보자::

    /yourapplication
        /yourapplication.py
        /static
            /style.css
        /templates
            layout.html
            index.html
            login.html
            ...

간단한 패키지
---------------

작은 어플리케이션을 큰 어플리케이션 구조로 변환하기 위해, 단지 기존에 존재하던 폴더에
새 폴더 `yourapplication` 를 생성하고 그 폴더로 모두 옯긴다.
그리고 나서, `yourapplication.py` 를 `__init__.py` 으로 이름을 바꾼다. 
(먼저 모든 `.pyc` 을 삭제해야지, 그렇지 않으면 모든 파일이 깨질 가능성이 크다.)

여러분은 아래와 같은 구조를 최종적으로 보게 될 것이다::

    /yourapplication
        /yourapplication
            /__init__.py
            /static
                /style.css
            /templates
                layout.html
                index.html
                login.html
                ...

하지만 이 상황에서 여러분은 어떻게 어플리케이션을 실행하는가?
``python yourapplication/__init__.py`` 와 같은 순진한 명령은 실행되지 않을 것이다.

파이썬은 패키지에 있는 모듈이 스타트업 파일이 되는 것을 원하지 않는다고 해보자.
하지만, 그것은 큰 문제는 아니고, 아래와 같이 단지 `runserver.py` 라는 새 파일을 
루트 폴더 바로 아래 있는 `yourapplication` 폴더 안에 추가하기만 하면 된다::

    from yourapplication import app
    app.run(debug=True)

이렇게해서 우리는 무엇을 얻었는가? 
이제 우리는 이 어플리케이션을 복개의 모듈들로 재구조화할 수 있다.
여러분이 기억해야할 유일한 것은 다음의 체크리스트이다::

1. `플라스크` 어플리케이션 객체 생성은 `__init__.py` 파일에서 해야한다.  
   그런 방식으로 개별 모듈은 안전하게 포함되고 `__name__` 변수는 알맞은 패키지로 해석될 것이다.
2. 모든 뷰 함수들은(함수의 선언부 위에 :meth:`~flask.Flask.route` 데코레이터(decorator)를 가진 
   함수)는 `__init__.py` 파일에 임포트되어야 하는데, 객체가 아닌 함수가 있는 모듈을 
   임포트해야한다. **어플리케이션 객체를 생성한 후에** 뷰 모듈을 임포트해라.

여기에 `__init__.py` 파일의 예제가 있다::

    from flask import Flask
    app = Flask(__name__)

    import yourapplication.views

그리고 아래가 `views.py` 파일의 예제일 수 있다::

    from yourapplication import app

    @app.route('/')
    def index():
        return 'Hello World!'

여러분은 최종적으로 아래와 같은 구조를 얻을 것이다::

    /yourapplication
        /runserver.py
        /yourapplication
            /__init__.py
            /views.py
            /static
                /style.css
            /templates
                layout.html
                index.html
                login.html
                ...

.. admonition:: 순환 임포트(Circular Imports)

   모든 파이썬 프로그래머는 순환 임포트를 싫어하지만, 우리는 일부 그것을 더했다:
   순환 임포트는(두 모듈이 서로 의존 관계가 있는 경우이다. 위 경우 `views.py` 는 `__init__.py` 에 의존한다).
   Be advised that this is a bad idea in general but here it is actually fine.
   이런 방식은 일반적으로 나쁘지만, 이 경우는 실제로 괜찮다고 생각해도 된다.
   왜냐하면 `__init__.py`에 있는 뷰들을 실제로 사용하지 않고 단지 모듈들이 임포트되었는지
   보장하고 그 파일의 제일 하단에서 임포트하기 때문이다.
   
   There are still some problems with that approach but if you want to use
   decorators there is no way around that.  Check out the
   :ref:`becomingbig` section for some inspiration how to deal with that.
   이런 접근법에도 일부 문제가 남아있지만 여러분이 데코레이터(decoroator)를 사용하고 싶다면
   문제를 피할 방도는 없다. 그것을 다루는 방법에 대한 몇 가지 영감을 위해 :ref:`becomingbig` 단락을 확인해라

.. _working-with-modules:

Working with Blueprints
-----------------------

If you have larger applications it's recommended to divide them into
smaller groups where each group is implemented with the help of a
blueprint.  For a gentle introduction into this topic refer to the
:ref:`blueprints` chapter of the documentation.
