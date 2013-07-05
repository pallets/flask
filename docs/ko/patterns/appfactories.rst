.. _app-factories:

어플리케이션 팩토리
=====================

여러분이 어플리케이션에 이미 패키지들과 청사진들을 사용한다면(:ref:`blueprints`) 
그 경험들을 좀 더 개선할 몇 가지 정말 좋은 방법들이 있다.
일반적인 패턴은 청사진을 임포트할 때 어플리케이션 객체를 생성하는 것이다.
하지만 여러분이 이 객체의 생성을 함수로 옮긴다면, 
나중에 이 객체에 대한 복수 개의 인스턴스를 생성할 수 있다.

그래서 여러분은 왜 이렇게 하고 싶은 것인가?

1.  테스팅.  여러분은 모든 케이스를 테스트하기 위해 여러 설정을 가진 어플리케이션 인스턴스들을 가질수 있다.
2.  복수 개의 인스턴스.  여러분이 같은 어플리케이션의 여러 다른 버전을 실행하고 싶다고 가정하자.
    물론 여러분은 여러분은 웹서버에 여러 다른 설정을 가진 복수 개의 인스턴스를 가질 수도 있지만, 
    여러분이 팩토리를 사용한다면, 여러분은 간편하게 같은 어플리케이션 프로세스에서 동작하는 
    복수 개의 인스턴스를 가질 수 있다.

그렇다면 어떻게 여러분은 실제로 그것을 구현할 것인가?

기본 팩토리
---------------

이 방식은 함수 안에 어플리케이션을 설정하는 방법이다::

    def create_app(config_filename):
        app = Flask(__name__)
        app.config.from_pyfile(config_filename)

        from yourapplication.views.admin import admin
        from yourapplication.views.frontend import frontend
        app.register_blueprint(admin)
        app.register_blueprint(frontend)

        return app

이 방식의 단점은 여러분은 임포트하는 시점에 청사진 안에 있는 어플리케이션 객체를 사용할 수 없다.
그러나 여러분은 요청 안에서 어플리케이션 객체를 사용할 수 있다.
어떻게 여러분이 설정을 갖고 있는 어플리케이션에 접근하는가? :data:`~flask.current_app` 을 사용하면 된다::

    from flask import current_app, Blueprint, render_template
    admin = Blueprint('admin', __name__, url_prefix='/admin')

    @admin.route('/')
    def index():
        return render_template(current_app.config['INDEX_TEMPLATE'])

여기에서 우리는 설정에 있는 템플릿 이름을 찾아낸다.

어플리케이션(Application) 사용하기
-----------------------------------

그렇다면 그런 어플리케이션을 사용하기 위해서 어려분은 먼저 어플리케이션을 생성해야한다.
아래는 그런 어플리케이션을 실행하는 `run.py` 파일이다::

    from yourapplication import create_app
    app = create_app('/path/to/config.cfg')
    app.run()

팩토리 개선
--------------------

위에서 팩토리 함수는 지금까지는 그다지 똑똑하지 않았지만, 여러분은 개선할 수 있다.
다음 변경들은 간단하고 가능성이 있다:

1.  여러분이 파일시스템에 설정 파일을 만들지 않도록 유닛테스트를 위해 설정값을 전달하도록 만들어라.
2.  여러분이 어플리케이션의 속성들을 변경할 곳을 갖기 위해 어플리케이션이 셋업될 때 청사진에서 함수를 호출해라.
    (요청 핸들러의 앞/뒤로 가로채는 것 처럼)
3.  필요하다면 어플리케이션이 생성될 때, WSGI 미들웨어에 추가해라.
