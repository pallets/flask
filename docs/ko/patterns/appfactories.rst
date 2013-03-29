.. _app-factories:

어플리케이션 팩토리
=====================

여러분이 어플리케이션에 이미 패키지들과 청사진들을 사용한다면(:ref:`blueprints`) 
그 경험들을 좀 더 개선할 몇 가지 정말 좋은 방법들이 있다.
일반적인 패턴은 청사진을 임포트할 때 어플리케이션 객체를 생성하는 것이다.
하지만 여러분이 이 객체의 생성을 함수로 옮긴다면, 
나중에 이 객체에 대한 복수 개의 인스턴스를 생성할 수 있다.

그래서 여러분은 왜 이렇게 하고 싶은 것인가?

1.  Testing.  You can have instances of the application with different
    settings to test every case.
2.  Multiple instances.  Imagine you want to run different versions of the
    same application.  Of course you could have multiple instances with
    different configs set up in your webserver, but if you use factories,
    you can have multiple instances of the same application running in the
    same application process which can be handy.

So how would you then actually implement that?

Basic Factories
---------------

The idea is to set up the application in a function.  Like this::

    def create_app(config_filename):
        app = Flask(__name__)
        app.config.from_pyfile(config_filename)

        from yourapplication.views.admin import admin
        from yourapplication.views.frontend import frontend
        app.register_blueprint(admin)
        app.register_blueprint(frontend)

        return app

The downside is that you cannot use the application object in the blueprints
at import time.  You can however use it from within a request.  How do you
get access to the application with the config?  Use
:data:`~flask.current_app`::

    from flask import current_app, Blueprint, render_template
    admin = Blueprint('admin', __name__, url_prefix='/admin')

    @admin.route('/')
    def index():
        return render_template(current_app.config['INDEX_TEMPLATE'])

Here we look up the name of a template in the config.

Using Applications
------------------

So to use such an application you then have to create the application
first.  Here an example `run.py` file that runs such an application::

    from yourapplication import create_app
    app = create_app('/path/to/config.cfg')
    app.run()

Factory Improvements
--------------------

The factory function from above is not very clever so far, you can improve
it.  The following changes are straightforward and possible:

1.  make it possible to pass in configuration values for unittests so that
    you don't have to create config files on the filesystem
2.  call a function from a blueprint when the application is setting up so
    that you have a place to modify attributes of the application (like
    hooking in before / after request handlers etc.)
3.  Add in WSGI middlewares when the application is creating if necessary.
