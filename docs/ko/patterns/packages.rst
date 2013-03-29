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

What did we gain from this?  Now we can restructure the application a bit
into multiple modules.  The only thing you have to remember is the
following quick checklist:

1. `플라스크` 어플리케이션 객체 생성은 `__init__.py` 파일에서 해야한다.  
   그런 방식으로 개별 모듈은 안전하게 포함되고 `__name__` 변수는 알맞은 패키지로 해석될 것이다.
2. all the view functions (the ones with a :meth:`~flask.Flask.route`
   decorator on top) have to be imported in the `__init__.py` file.
   Not the object itself, but the module it is in. Import the view module
   **after the application object is created**.

Here's an example `__init__.py`::

    from flask import Flask
    app = Flask(__name__)

    import yourapplication.views

And this is what `views.py` would look like::

    from yourapplication import app

    @app.route('/')
    def index():
        return 'Hello World!'

You should then end up with something like that::

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

.. admonition:: Circular Imports

   Every Python programmer hates them, and yet we just added some:
   circular imports (That's when two modules depend on each other.  In this
   case `views.py` depends on `__init__.py`).  Be advised that this is a
   bad idea in general but here it is actually fine.  The reason for this is
   that we are not actually using the views in `__init__.py` and just
   ensuring the module is imported and we are doing that at the bottom of
   the file.

   There are still some problems with that approach but if you want to use
   decorators there is no way around that.  Check out the
   :ref:`becomingbig` section for some inspiration how to deal with that.


.. _working-with-modules:

Working with Blueprints
-----------------------

If you have larger applications it's recommended to divide them into
smaller groups where each group is implemented with the help of a
blueprint.  For a gentle introduction into this topic refer to the
:ref:`blueprints` chapter of the documentation.
