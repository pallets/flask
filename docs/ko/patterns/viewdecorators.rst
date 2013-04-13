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

이 예제는 
This example assumes that the login page is called ``'login'`` and that
the current user is stored as `g.user` and `None` if there is no-one
logged in::

    from functools import wraps
    from flask import g, request, redirect, url_for

    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if g.user is None:
                return redirect(url_for('login', next=request.url))
            return f(*args, **kwargs)
        return decorated_function

So how would you use that decorator now?  Apply it as innermost decorator
to a view function.  When applying further decorators, always remember
that the :meth:`~flask.Flask.route` decorator is the outermost::

    @app.route('/secret_page')
    @login_required
    def secret_page():
        pass

Caching Decorator
-----------------

Imagine you have a view function that does an expensive calculation and
because of that you would like to cache the generated results for a
certain amount of time.  A decorator would be nice for that.  We're
assuming you have set up a cache like mentioned in :ref:`caching-pattern`.

Here an example cache function.  It generates the cache key from a
specific prefix (actually a format string) and the current path of the
request.  Notice that we are using a function that first creates the
decorator that then decorates the function.  Sounds awful? Unfortunately
it is a little bit more complex, but the code should still be
straightforward to read.

The decorated function will then work as follows

1. get the unique cache key for the current request base on the current
   path.
2. get the value for that key from the cache. If the cache returned
   something we will return that value.
3. otherwise the original function is called and the return value is
   stored in the cache for the timeout provided (by default 5 minutes).

Here the code::

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

Notice that this assumes an instantiated `cache` object is available, see
:ref:`caching-pattern` for more information.


Templating Decorator
--------------------

A common pattern invented by the TurboGears guys a while back is a
templating decorator.  The idea of that decorator is that you return a
dictionary with the values passed to the template from the view function
and the template is automatically rendered.  With that, the following
three examples do exactly the same::

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

As you can see, if no template name is provided it will use the endpoint
of the URL map with dots converted to slashes + ``'.html'``.  Otherwise
the provided template name is used.  When the decorated function returns,
the dictionary returned is passed to the template rendering function.  If
`None` is returned, an empty dictionary is assumed, if something else than
a dictionary is returned we return it from the function unchanged.  That
way you can still use the redirect function or return simple strings.

Here the code for that decorator::

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


Endpoint Decorator
------------------

When you want to use the werkzeug routing system for more flexibility you
need to map the endpoint as defined in the :class:`~werkzeug.routing.Rule` 
to a view function. This is possible with this decorator. For example:: 

    from flask import Flask
    from werkzeug.routing import Rule

    app = Flask(__name__)                                                          
    app.url_map.add(Rule('/', endpoint='index'))                                   

    @app.endpoint('index')                                                         
    def my_index():                                                                
        return "Hello world"     



