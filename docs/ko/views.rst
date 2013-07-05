.. _views:

플러거블 뷰(Pluggable Views)
===============

.. versionadded:: 0.7

플라스크 0.7은 함수가 아닌 클래스를 기반으로한 Django 프레임워크의 제너릭 뷰(generic view)에 
영향을 받은 플러거블 뷰(pluggable view : 끼워넣는 뷰)를 소개한다. 이 뷰의 주 목적는 
여러분이 구현체의 부분들을 바꿀수 있고 이 방식으로 맞춤과 끼워넣는것이 가능한 뷰를 갖는 
것이다. 


기본 원칙(Basic Principle)
---------------

여러분이 데이타베이스에서 어떤 객체의 목록을 읽어서 템플릿에 보여주는 함수를 가진다고 고려해보자::

    @app.route('/users/')
    def show_users(page):
        users = User.query.all()
        return render_template('users.html', users=users)

위의 코드는 간단하고 유연하지만, 여러분이 다른 모델이나 템플릿에도 적용가능한 일반적인 
방식으로 이 뷰를 제공하고 싶다면 더 유연한 구조를 원할지 모른다. 이 경우가 끼워넣을 수 있는 
클래스를 기반으로 한 뷰가 적합한 곳이다. 클래스 기반의 뷰로 변환하기 위한 첫 단계는 아래와 
같다. ::


    from flask.views import View

    class ShowUsers(View):

        def dispatch_request(self):
            users = User.query.all()
            return render_template('users.html', objects=users)

    app.add_url_rule('/users/', view_func=ShowUsers.as_view('show_users'))


위에서 볼 수 있는 것처럼, 여러분은 :class:`flask.views.View` 의 서브클래스를 만들고 
:meth:`~flask.views.View.dispatch_request` 를 구현해야한다. 그리고 그 클래스를 
:meth:`~flask.views.View.as_view` 클래스 메소드를 사용해서 실제 뷰 함수로 변환해야한다.
 그 함수로 전달하는 문자열은 뷰가 가질 끝점(end-point)의 이름이다. 위의 코드를 조금 
 리팩토링해보자. ::

    
    from flask.views import View

    class ListView(View):

        def get_template_name(self):
            raise NotImplementedError()

        def render_template(self, context):
            return render_template(self.get_template_name(), **context)

        def dispatch_request(self):
            context = {'objects': self.get_objects()}
            return self.render_template(context)

    class UserView(ListView):

        def get_template_name(self):
            return 'users.html'

        def get_objects(self):
            return User.query.all()


물론 이것은 이런 작은 예제에서는 그다지 도움이 안될 수도 있지만, 기본 원칙을 설명하기에는 
충분하다. 여러분이 클래스 기반의 뷰를 가질 때, `self` 가 가리키는 건 무엇이냐는 질문이 
나온다. 이것이 동작하는 방식은 요청이 들어올 때마다 클래스의 새 인스턴스가 생성되고 
:meth:`~flask.views.View.dispatch_request` 메소드가 URL 규칙으로부터 나온 인자를 
가지고 호출된다. 클래스 그 자체로는 :meth:`~flask.views.View.as_view` 함수에 넘겨지는 
인자들을 가지고 인스턴스화된다. 예를 들면, 아래와 같은 클래스를 작성할 수 있다::


    class RenderTemplateView(View):
        def __init__(self, template_name):
            self.template_name = template_name
        def dispatch_request(self):
            return render_template(self.template_name)

그런 다음에 여러분은 아래와 같이 뷰 함수를 등록할 수 있다:: 


    app.add_url_rule('/about', view_func=RenderTemplateView.as_view(
        'about_page', template_name='about.html'))



메소드 힌트
------------
끼워넣을수 있는 뷰는 :func:`~flask.Flask.route` 나 더 낫게는 
:meth:`~flask.Flask.add_url_rule`을 사용하여 보통 함수처럼 어플리케이션에 덧붙여진다. 
하지만, 그것은 또한 여러분이 이 뷰를 덧붙였을 때 뷰가 지원하는 HTTP 메소드들의 이름을 
제공해줘야 하는 것을 의미한다. 그 정보를 클래스로 옮기기 위해, 여러분은 이 정보를 갖고 있는 
:attr:`~flask.views.View.methods` 속성 정보를 제공할 수 있다::


    class MyView(View):
        methods = ['GET', 'POST']

        def dispatch_request(self):
            if request.method == 'POST':
                ...
            ...

    app.add_url_rule('/myview', view_func=MyView.as_view('myview'))


메소드 기반 디스패치
------------------------

RESTful API에서 각 HTTP 메소드별로 다른 함수를 수행하는 것은 굉장히 도움이 된다. 
:class:`flask.views.MethodView` 로 여러분은 그 작업을 쉽게 할 수 있다. 각 HTTP 
메소드는 같은 이름을 가진 함수(소문자)로 연결된다. ::


    from flask.views import MethodView

    class UserAPI(MethodView):

        def get(self):
            users = User.query.all()
            ...

        def post(self):
            user = User.from_form_data(request.form)
            ...

    app.add_url_rule('/users/', view_func=UserAPI.as_view('users'))

이 방식은 또한 여러분이 :attr:`~flask.views.View.methods` 속성을 제공하지 않아도 된다. 
클래스에 정의된 메소드 기반으로 자동으로 설정된다. 


데코레이팅 뷰
----------------

뷰 클래스 그 자체는 라우팅 시스템에 추가되는 뷰 함수가 아니기 때문에, 클래스 자체를 
데코레이팅하는 것은 이해되지 않는다. 대신, 여러분이 수동으로 :meth:`~flask.views.View.as_view` 함수의 리턴값을 데코레이팅해야한다::


    def user_required(f):
        """Checks whether user is logged in or raises error 401."""
        def decorator(*args, **kwargs):
            if not g.user:
                abort(401)
            return f(*args, **kwargs)
        return decorator

    view = user_required(UserAPI.as_view('users'))
    app.add_url_rule('/users/', view_func=view)

플라스크 0.8부터 클래스 선언에도 적용할 데코레이터 목록을 표시할 수 있는 대안이 있다::

    class UserAPI(MethodView):
        decorators = [user_required]

호출하는 입장에서 그 자체로 암시적이기 때문에 여러분이 뷰의 개별 메소드에 일반적인 뷰 
데코레이터를 사용할 수 없다는 것을 명심하길 바란다. 


메소드 뷰 API
---------------------

웹 API는 보통 HTTP 메소드와 매우 밀접하게 동작하는데 
:class:`~flask.views.MethodView` 기반의 API를 구현할때는 
더욱 의미가 들어맞는다. 그렇긴 하지만, 여러분은 그 API가 대부분 같은 메소드 뷰로 가는 여러 
다른 URL 규칙을 요구할 것이라는 것을 알아야 할 것이다. 예를 들면, 여러분이 웹에서 사용자 
객체에 노출된 상황을 고려해보자: 



=============== =============== ======================================
URL             Method          Description
--------------- --------------- --------------------------------------
``/users/``     ``GET``         전체 사용자 정보 목록 얻기 
``/users/``     ``POST``        새로운 사용자 정보 생성 
``/users/<id>`` ``GET``          단일 사용자 정보 얻기 
``/users/<id>`` ``PUT``         단일 사용자 정보 갱신 
``/users/<id>`` ``DELETE``      단일 사용자 정보 삭제
=============== =============== ======================================

그렇다면 :class:`~flask.views.MethodView` 를 가지고는 어떻게 위와 같은 작업을 계속할 
것인가? 여러분이 같은 뷰에 여러 규칙을 제공할 수 있는 것이 요령이다.

뷰가 아래와 같이 보일 때를 가정해보자::


    class UserAPI(MethodView):

        def get(self, user_id):
            if user_id is None:
                # return a list of users
                pass
            else:
                # expose a single user
                pass

        def post(self):
            # create a new user
            pass

        def delete(self, user_id):
            # delete a single user
            pass

        def put(self, user_id):
            # update a single user
            pass


그렇다면 우리는 이것을 어떻게 라우팅 시스템으로 연결하는가? 두가지 규칙을 추가하고 
명시적으로 각 메소드를 언급한다:: 


    user_view = UserAPI.as_view('user_api')
    app.add_url_rule('/users/', defaults={'user_id': None},
                     view_func=user_view, methods=['GET',])
    app.add_url_rule('/users/', view_func=user_view, methods=['POST',])
    app.add_url_rule('/users/<int:user_id>', view_func=user_view,
                     methods=['GET', 'PUT', 'DELETE'])



여러분이 유사하게 보이는 여러 API를 갖고 있다면, 등록하는 메소드를 추가하도록 아래처럼 
리팩토링할 수 있다::

    def register_api(view, endpoint, url, pk='id', pk_type='int'):
        view_func = view.as_view(endpoint)
        app.add_url_rule(url, defaults={pk: None},
                         view_func=view_func, methods=['GET',])
        app.add_url_rule(url, view_func=view_func, methods=['POST',])
        app.add_url_rule('%s<%s:%s>' % (url, pk_type, pk), view_func=view_func,
                         methods=['GET', 'PUT', 'DELETE'])

    register_api(UserAPI, 'user_api', '/users/', pk='user_id')
