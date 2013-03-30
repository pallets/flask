URL 프로세서 이용하기
====================

.. versionadded:: 0.7

플라스크 0.7 은 URL 프로세서의 개념을 소개한다. 이 방식은 여러분이 항상
명시적으로 제공하기를 원하지 않는 URL의 공통 부분을 포함하는 여러 리소스를 
가질 수 있다는 것이다.  예를 들면, 여러분은 URL 안에 언어 코드를 갖지만
모든 개별 함수에서 그것을 처리하고 싶지않은 다수의 URL을 가질 수 있다. 

청사진과 결합될 때, URL 프로세서는 특히나 도움이 된다. 청사진이 지정된
URL 프로세서 뿐만아니라 어플리케이션이 지정된 URL 프로세서 둘 다 다룰 것이다.

국제화된 어플리케이션 URL
-------------------------

아래와 같은 어플리케이션을 고려해보자::

    from flask import Flask, g

    app = Flask(__name__)

    @app.route('/<lang_code>/')
    def index(lang_code):
        g.lang_code = lang_code
        ...

    @app.route('/<lang_code>/about')
    def about(lang_code):
        g.lang_code = lang_code
        ...

이것은 여러분이 모든 개별 함수마다 :data:`~flask.g` 객체에 언어 코드 설정을
처리해야하기 때문에 엄청나게 많은 반복이다. 물론, 데코레이터가 이런 작업을
간단하게 만들어 줄 수 있지만, 여러분이 하나의 함수에서 다른 함수로 URL을
생성하고 싶다면, 여러분은 언어 코드를 명시적으로 제공하는 성가신 작업을
여전히 해야한다.

후자의 경우, :func:`~flask.Flask.url_defaults` 가 관여하는 곳 이다.
그것들은 자동으로 :func:`~flask.url_for` 호출에 대해 값을 주입한다.
아래의 코드는 언어 코드가 URL 딕셔너리에는 아직 없는지와 끝점(endpoint)가 
``'lang_code'` 라는 변수의 값을 원하는지를 확인한다::

    @app.url_defaults
    def add_language_code(endpoint, values):
        if 'lang_code' in values or not g.lang_code:
            return
        if app.url_map.is_endpoint_expecting(endpoint, 'lang_code'):
            values['lang_code'] = g.lang_code

URL 맵에 대한 :meth:`~werkzeug.routing.Map.is_endpoint_expecting` 메소드는
주어진 끝점에 대해 언어 코드를 제공하는 것이 적합한지 확인하는데 사용된다.

위의 함수와 반대되는 함수로는 :meth:`~flask.Flask.url_value_preprocessor` 가 있다.
그것들은 요청이 URL과 매치된 후에 바로 실행되고 URL 값에 기반된 코드를 실행할 수 있다.
이 방식은 그 함수들이 딕셔너리로 부터 값을 꺼내고 다른 곳에 그 값을 넣는 것이다::

    @app.url_value_preprocessor
    def pull_lang_code(endpoint, values):
        g.lang_code = values.pop('lang_code', None)

이 방식으로 여러분은 더 이상 모든 함수에서 :data:`~flask.g` 에 `lang_code` 를 
할당하지 않아도 된다. 여러분은 You can further improve that by
writing your own decorator that prefixes URLs with the language code, but
the more beautiful solution is using a blueprint.  Once the
``'lang_code'`` is popped from the values dictionary and it will no longer
be forwarded to the view function reducing the code to this::

    from flask import Flask, g

    app = Flask(__name__)

    @app.url_defaults
    def add_language_code(endpoint, values):
        if 'lang_code' in values or not g.lang_code:
            return
        if app.url_map.is_endpoint_expecting(endpoint, 'lang_code'):
            values['lang_code'] = g.lang_code

    @app.url_value_preprocessor
    def pull_lang_code(endpoint, values):
        g.lang_code = values.pop('lang_code', None)

    @app.route('/<lang_code>/')
    def index():
        ...

    @app.route('/<lang_code>/about')
    def about():
        ...

Internationalized Blueprint URLs
--------------------------------

Because blueprints can automatically prefix all URLs with a common string
it's easy to automatically do that for every function.  Furthermore
blueprints can have per-blueprint URL processors which removes a whole lot
of logic from the :meth:`~flask.Flask.url_defaults` function because it no
longer has to check if the URL is really interested in a ``'lang_code'``
parameter::

    from flask import Blueprint, g

    bp = Blueprint('frontend', __name__, url_prefix='/<lang_code>')

    @bp.url_defaults
    def add_language_code(endpoint, values):
        values.setdefault('lang_code', g.lang_code)

    @bp.url_value_preprocessor
    def pull_lang_code(endpoint, values):
        g.lang_code = values.pop('lang_code')

    @bp.route('/')
    def index():
        ...

    @bp.route('/about')
    def about():
        ...
