지연 로딩 뷰(Lazily Loading Views)
==================================

플라스크는 보통 데코레이터를 가지고 사용된다.  데코레이터는 간단하고 
여러분은 특정 URL에 대해 호출되는 함수 바로 옆에 URL을 놓게 된다.
그러나 이런 방식에 단점이 있다: 데코레이터를 사용하는 여러분의 모든 코드가
가장 앞단에서 임포트되어야 하고 그렇지 않다면 플라스크는 실제로 여러분의
함수를 결코 찾지 못할 것이다.

여러분의 어플리케이션이 빠르게 임포트되어야 한다면 이것은 문제가 될 수 있다.
구글 앱 엔진이나 다른 시스템처럼 그 자체가 그 임포트를 해야할 지도 모른다.
그렇기 때문에 여러분의 어플리케이션이 규모가 커져서 이 방식이 더 이상 
맞지 않다는 것을 갑자기 알게된다면 여러분은 중앙집중식 URL 매핑으로 되돌아
갈 수 도 있다.

중앙식 URL 맴을 갖도록 활성화하는 시스템은 :meth:`~flask.Flask.add_url_rule`
함수이다.  데코레이터를 사용하는 대신, 여러분은 어플리케이션의 모든 URL을 
파일로 갖을 수 있다.

중앙집중식 URL 맴으로 변환하기
------------------------------

현재 어플리케이션이 아래와 같은 모습이라고 상상해보자::

    from flask import Flask
    app = Flask(__name__)

    @app.route('/')
    def index():
        pass

    @app.route('/user/<username>')
    def user(username):
        pass

그렇다면 중앙집중 방식에서는 여러분은 데코레이터가 없는 뷰를 가진 하나의 
파일 (`views.py`) 을 가질 것이다::

    def index():
        pass

    def user(username):
        pass

그렇다면 URL과 함수를 매핑하는 어플리케이션을 설정하는 파일을 다음과 같다::

    from flask import Flask
    from yourapplication import views
    app = Flask(__name__)
    app.add_url_rule('/', view_func=views.index)
    app.add_url_rule('/user/<username>', view_func=views.user)

늦은 로딩
---------

지금까지 우리는 단지 뷰와 라우팅만 분리했지만, 모듈은 여전히 처음에 로딩된다.
필요할 때 뷰 함수가 실제 로딩되는 기법이 있다.  이것은 함수와 같이 동작하는
도움 클래스와 같이 수행될 수 있지만, 내부적으로 첫 사용에는 실제 함수를
임포는 한다::

    from werkzeug import import_string, cached_property

    class LazyView(object):

        def __init__(self, import_name):
            self.__module__, self.__name__ = import_name.rsplit('.', 1)
            self.import_name = import_name

        @cached_property
        def view(self):
            return import_string(self.import_name)

        def __call__(self, *args, **kwargs):
            return self.view(*args, **kwargs)

여기서 중요한 것은 `__module__` 과 `__name__` 알맞게 설정되야 한다.
이것은 여러분이 URL 규칙에 대한 이름을 제공하는 않는 경우에 플라스크가 
내부적으로 URL 규칙을 이름짓는 방식을 알기 위해 사용된다.

그리고 나서 여러분은 아래처럼 뷰와 결합할 중앙위치를 정의할 수 있다:

    from flask import Flask
    from yourapplication.helpers import LazyView
    app = Flask(__name__)
    app.add_url_rule('/',
                     view_func=LazyView('yourapplication.views.index'))
    app.add_url_rule('/user/<username>',
                     view_func=LazyView('yourapplication.views.user'))

여러분은 키보드로 입력하는 코드의 양이라는 측면에서 프로젝트 명과 점(dot)을
접두어화하고 필요에 따라 `LazyView` 에 있는 `view_func` 을 래핑한 것으로
:meth:`~flask.Flask.add_url_rule` 을 호출하는 함수를 작성함으로 이것을 
더 최적화할 수 있다::

    def url(url_rule, import_name, **options):
        view = LazyView('yourapplication.' + import_name)
        app.add_url_rule(url_rule, view_func=view, **options)

    url('/', 'views.index')
    url('/user/<username>', 'views.user')

한가지 명심해야할 것은 전후 요청 핸들러가 첫 요청에 올바르게 동작하기 위해
앞단에서 임포트되는 파일에 있어야 한다는 것이다.  나머지 데코레이터도 같은
방식이 적용된다.
