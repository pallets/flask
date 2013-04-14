뷰 데코레이터(View Decorators)
==============================

파이썬에는 함수 데코레이터라 불리는 꽤 흥미로운 기능이 있다.  이 기능은
웹 어플리케이션에서 정말 깔끔한 기능을 허용한다.  플라스크 각 뷰는 한 개 
이상의 함수에 추가적인 기능을 주입하는데 사용될 수 있는 함수 데코레이터
이기 때문인다.  여러분은 이미 :meth:`~flask.Flask.route` 데코레이터를
사용했을 것이다.  하지만 여러분 자신만의 데코레이터를 구현하는 몇가지
사용법이 있다.  예를 들면, 로그인한 사람들에게만 사용되야하는 뷰가 있다고
하자.  사용자가 해당 사이트로 가서 로그인 하지 않았다면, 그 사용자는 
로그인 페이지로 리디렉션 되어야한다.  이런 상황이 데코레이터가 훌륭한
해결책이 되는 사용법의 좋은 예이다.

로그인이 필수적인 데코레이터
----------------------------

자 그렇다면 그런 데코레이터를 구현해보자.  데코레이터는 함수를 반환하는
함수이다.  사실 꽤 간단한 개념이다.  이런것을 구현할 때 꼭 유념해야할
것은 `__name__`, `__module__` 그리고 함수의 몇 가지 다른 속성들이다.
이런 것을 자주 잊곤하는데, 수동으로 그것을 할 필요는 없고, 그것을 해주는
데코레이터처럼 사용되는 함수가 있다 (:func:`functools.wraps`).

이 예제는 로그인 페이지를 ``login`` 이라하고 현재 사용자는 `g.user` 로
저장돼있으며 로그인되지 않았다면 `None` 이 저장된다고 가정한다::

    from functools import wraps
    from flask import g, request, redirect, url_for

    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if g.user is None:
                return redirect(url_for('login', next=request.url))
            return f(*args, **kwargs)
        return decorated_function

그렇다면 여러분은 여기서 그 데코레이터를 어떻게 사용하겠는가?  뷰 함수의
가장 안쪽에 있는 데코레이터로 사용하면 된다.  더 나아가서 적용할 때,
:meth:`~flask.Flask.route` 데코레이터가 가장 바깥에 있다는 것을 기억해라::

    @app.route('/secret_page')
    @login_required
    def secret_page():
        pass

캐싱 데코레이터
---------------

여러분이 시간이 많이 소요되는 계산을 하는 뷰 함수를 가지고 있고 그것 때문에
일정 시간동안 계산된 결과를 캐시하고 싶다고 생각해보자.  이런 경우 데코레이터가
멋지게 적용될 수 있다. 우리는 여러분이 :ref:`caching-pattern` 라 언급한 캐시를
만든다고 가정할 것이다.

여기에 캐시 함수의 예제가 있다.  그 캐시 함수는 특정 접두어(형식이 있는 문자열)
로부터 캐시 키와 요청에 대한 현재 경로를 생성한다.  먼저 함수 자체를 데코레이트하는
데코레이터를 먼저 생성하는 함수를 사용하고 있다는 것에 주목해라.  끔찍하게 
들리는가?  불행히도 약간 더 복잡하지만, 그 코드는 읽기엔 여전히 직관적일 것이다.

데코레이트된 함수는 다음과 같이 동작할 것이다

1. 현재 경로에 기반한 현재 요청에 대한 유일한 캐시 키를 얻는다.
2. 캐시에서 그 키에 대한 값을 얻는다.  캐시가 어떤값을 반환하면
   우리는 그 값을 반환할 것이다.
3. 그 밖에는 원본 함수가 호출되고 반환값은 주어진 타임아웃 
   (기본값 5분) 동안 캐시에 저장된다. 

여기 코드가 있다::

    from functools import wraps
    from flask import request

    def cached(timeout=5 * 60, key='view/%s'):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                cache_key = key % request.path
                rv = cache.get(cache_key)
                if rv is not None:
                    return rv
                rv = f(*args, **kwargs)
                cache.set(cache_key, rv, timeout=timeout)
                return rv
            return decorated_function
        return decorator

이 함수는 인스턴스화된 `cache` 객체가 사용 가능하다고 가정한다는 것에
주목하고, 더 많은 정보는 :ref:`caching-pattern` 을 살펴봐라.


데코레이터를 템플화하기 
-----------------------

일전에 터보기어스(TurboGears) 친구들이 고안한 공통 패턴이 데코레이터
템플릿화이다.  그 데코레이터의 방식은 여러분은 뷰 함수로부터 템플릿에
넘겨질 값들을 가진 딕셔너리를 반환하고 그 템플릿은 자동으로 값을 
화면에 뿌려준다.  그 템플릿으로, 아래 세가지 예제는 정확히 같은 동작을
한다::

    @app.route('/')
    def index():
        return render_template('index.html', value=42)

    @app.route('/')
    @templated('index.html')
    def index():
        return dict(value=42)

    @app.route('/')
    @templated()
    def index():
        return dict(value=42)

여러분이 볼 수 있는 것처럼, 템플릿 명이 없다면 URL 맵의 끝점의 점(dot)을
슬래쉬(/)로 바꾸고 ``'.html'`` 을 더해서 사용할 것이다.  데코레이트된
함수가 반환할 때, 반환된 딕셔너리는 템플릿 렌더링 함수에 넘겨진다.  
`None` 이 반환되고, 빈 딕셔너리를 가정한다면, 딕셔너리가 아닌 다른 것이 
반환된다면 우리는 변경되지 않는 함수에서 그것을 반환한다. 그 방식으로 
여러분은 여전히 리디렉트 함수를 사용하거나 간단한 문자열을 반환할 수 있다.

여기 그 데코레이터에 대한 코드가 있다::

    from functools import wraps
    from flask import request

    def templated(template=None):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                template_name = template
                if template_name is None:
                    template_name = request.endpoint \
                        .replace('.', '/') + '.html'
                ctx = f(*args, **kwargs)
                if ctx is None:
                    ctx = {}
                elif not isinstance(ctx, dict):
                    return ctx
                return render_template(template_name, **ctx)
            return decorated_function
        return decorator


끝점(Endpoint) 데코레이터
-------------------------

여러분이 더 유연함을 제공하는 벡자이크 라우팅 시스템을 사용하고 싶을 때
여러분은 :class:`~werkzeug.routing.Rule` 에 정의된 것 처럼 끝점을 뷰 함수와
맞출(map) 필요가 있다. 이것은 이 끝점 데코레이터와 함께 사용하여 가능하다.
예를 들면::

    from flask import Flask
    from werkzeug.routing import Rule

    app = Flask(__name__)                                                          
    app.url_map.add(Rule('/', endpoint='index'))                                   

    @app.endpoint('index')                                                         
    def my_index():                                                                
        return "Hello world"     



