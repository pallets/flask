.. _blueprints:

청사진을 가진 모듈화된 어플리케이션
===================================

.. versionadded:: 0.7

플라스크는 어플리케이션 컴포넌트를 만들고 어플리케이션 내부나 어플리케이션간에
공통 패턴을 지원하기 위해 *청사진(blueprint)* 라는 개념을 사용한다.  청사진은
보통 대형 어플리케이션이 동작하는 방식을 단순화하고 어플리케이션의 동작을
등록하기 위한 플라스크 확장에 대한 중앙 집중된 수단을 제공할 수 있다.
:class:`Blueprint` 객체는 :class:`Flask` 어플리케이션 객체와 유사하게 동작하지만
실제로 어플리케이션은 아니다. 다만 어플리케이션을 생성하거나 확장하는 방식에 대한
*청사진* 이다.

왜 청사진인가?
--------------

플라스크의 청사진은 다음 경우로 인해 만들어졌다:

* 어플리케이션을 청사진의 집합으로 고려한다.  이 방식은 대형 어플리케이션에 
  있어서 이상적이다; 프로젝트는 어플리케이션 객체를 인스턴스화하고,
  여러 확장을 초기화하고, 청사진의 묶음을 등록할 수 있다.
* 어플리케이션 상에 URL 접두어와/또는 서브도메인으로 청사진을 등록한다.
  URL 접두어와/또는 서브도메인에 있는 파라메터는 청사진에 있는 모든 뷰 함수에
  걸쳐있는 공통 뷰 인자(기본값을 가진)가 된다.
* 어플리케이션에 여러 URL 규칙을 가진 청사진을 여러번 등록한다.
* 청사진을 통해 템플릿 필터, 정적 파일, 템플릿, 그리고 다른 유틸리티를 제공한다.
  청사진은 어플리케이션이나 뷰 함수를 구현하지 않아도 된다.
* 플라스크 확장을 초기화할 때 이런 경우 중 어떤 경우라도 어플리케이션에 청사진을 
  등록한다.

플라스크에 있는 청사진은 끼우고 뺄수 있는 앱이 아니다 왜냐하면 청사진은 실제
어플리케이션이 아니기 때문이다 -- 그것은 어플리케이션에 등록될 수 있는 동작의
집합인데 심지어 여러번 등록될 수 있다.  왜 복수의 어플리케이션 객체를 가지지 
않는가?  여러분은 그렇게(:ref:`app-dispatch` 을 살펴봐라)할 수 있지만, 
어플리케이션은 분리된 설정을 가질것 이고 WSGI 계층에서 관리될 것이다.

대신에 청사진은 플라스크 레벨에서 분리를 제공하고, 어플리케이션 설정을 공유하며
, 그리고 등록된 것을 가지고 필요에 따라 어플리케이션 객체를 변경할 수 있다.
이것의 단점은 일단 전체 어플리케이션 객체를 제거할 필요없이 어플리케이션이
생성됐을 때 여러분은 청사진을 해지할 수 없다.

청사진의 개념
-------------

청사진의 기본 개념은 어플리케이션에 청사진이 등록될 때 실행할 동작을
기록한다는 것이다.  플라스크는 요청을 보내고 하나의 끝점에서 다른 곳으로
URL을 생성할 때 뷰 함수와 청사진의 연관을 맺는다. 

첫번째 청사진
-------------

아래는 가장 기본적인 청사진의 모습이다.  이 경우에 우리는 정적 템플릿을
간단하게 그려주는 청사진을 구현하기를 원할 것이다::

    from flask import Blueprint, render_template, abort
    from jinja2 import TemplateNotFound

    simple_page = Blueprint('simple_page', __name__,
                            template_folder='templates')

    @simple_page.route('/', defaults={'page': 'index'})
    @simple_page.route('/<page>')
    def show(page):
        try:
            return render_template('pages/%s.html' % page)
        except TemplateNotFound:
            abort(404)

``@simple_page.route`` 데코레이터와 함수를 연결할 때 청사진은 
어플리케이션에 있는 그  함수를 등록하겠다는 의도를 기록할 것이다.
게다가 청사진은 :class:`Blueprint` 생성자(위의 경우에는 ``simple_page``)
에 들어가는 그 이름을 가지고 등록된 함수의 끝점 앞에 붙일 것이다.


청사진 등록하기
---------------

그렇다면 청사진을 어떻게 등록할 것 인가? 아래와 같이 등록한다::

    from flask import Flask
    from yourapplication.simple_page import simple_page

    app = Flask(__name__)
    app.register_blueprint(simple_page)

여러분이 어플리케이션에 등록된 규칙을 확인한다면, 여러분은 아래와
같은 것을 찾을 것이다::

    [<Rule '/static/<filename>' (HEAD, OPTIONS, GET) -> static>,
     <Rule '/<page>' (HEAD, OPTIONS, GET) -> simple_page.show>,
     <Rule '/' (HEAD, OPTIONS, GET) -> simple_page.show>]

첫 규칙은 명시적으로 어플리케이션에 있는 정적 파일에 대한 것이다.
다른 두 규칙은 ``simple_page`` 청사진의 `show` 함수에 대한 것이다. 
볼 수 있는 것 처럼, 청사진의 이름이 접두어로 붙어있고 점 (``.``)
으로 구분되있다.

하지만 청사진은 또한 다른 지점으로 마운트 될 수 있도 있다::

    app.register_blueprint(simple_page, url_prefix='/pages')

그리고 물론 말할 것도 없이, 아래와 같은 규칙이 생성된다::

    [<Rule '/static/<filename>' (HEAD, OPTIONS, GET) -> static>,
     <Rule '/pages/<page>' (HEAD, OPTIONS, GET) -> simple_page.show>,
     <Rule '/pages/' (HEAD, OPTIONS, GET) -> simple_page.show>]

무엇보다 모든 청사진이 복수로 적용되는 것에 적절한 응답을 주지는 않지만
여러분은 청사진을 여러번 등록할 수 있다.  사실 한번 이상 청사진을 마운트할
수 있다면 제대로 청사진이 동작하느냐는 청사진을 어떻게 구현했으냐에 달려있다.

청사진 리소스
-------------

청사진은 리소스 또한 제공할 수 있다.  때때로 여러분은 단지 리소스만을
제공하기 위해 청사진을 사용하고 싶을 수도 있다.

청사진 리소스 폴더
``````````````````

보통 어플리케이션처럼, 청사진은 폴더안에 포함되도록 고려된다.  다수의
청사진이 같은 폴더에서 제공될 수 있지만, 그런 경우가 될 필요도 없고
보통 권고하지 않는다.

폴더는 보통 `__name__` 인 :class:`Blueprint` 에 두번째 인자로 생각된다.
이 인자는 어떤 논리적인 파이썬 모듈이나 패키지가 청사진과 상응되는지 
알려준다.  If it points to an actual
Python package that package (which is a folder on the filesystem) is the
resource folder.  If it's a module, the package the module is contained in
will be the resource folder.  You can access the
:attr:`Blueprint.root_path` property to see what the resource folder is::

    >>> simple_page.root_path
    '/Users/username/TestProject/yourapplication'

To quickly open sources from this folder you can use the
:meth:`~Blueprint.open_resource` function::

    with simple_page.open_resource('static/style.css') as f:
        code = f.read()

Static Files
````````````

A blueprint can expose a folder with static files by providing a path to a
folder on the filesystem via the `static_folder` keyword argument.  It can
either be an absolute path or one relative to the folder of the
blueprint::

    admin = Blueprint('admin', __name__, static_folder='static')

By default the rightmost part of the path is where it is exposed on the
web.  Because the folder is called ``static`` here it will be available at
the location of the blueprint + ``/static``.  Say the blueprint is
registered for ``/admin`` the static folder will be at ``/admin/static``.

The endpoint is named `blueprint_name.static` so you can generate URLs to
it like you would do to the static folder of the application::

    url_for('admin.static', filename='style.css')

Templates
`````````

If you want the blueprint to expose templates you can do that by providing
the `template_folder` parameter to the :class:`Blueprint` constructor::

    admin = Blueprint('admin', __name__, template_folder='templates')

As for static files, the path can be absolute or relative to the blueprint
resource folder.  The template folder is added to the searchpath of
templates but with a lower priority than the actual application's template
folder.  That way you can easily override templates that a blueprint
provides in the actual application.

So if you have a blueprint in the folder ``yourapplication/admin`` and you
want to render the template ``'admin/index.html'`` and you have provided
``templates`` as a `template_folder` you will have to create a file like
this: ``yourapplication/admin/templates/admin/index.html``.

Building URLs
-------------

If you want to link from one page to another you can use the
:func:`url_for` function just like you normally would do just that you
prefix the URL endpoint with the name of the blueprint and a dot (``.``)::

    url_for('admin.index')

Additionally if you are in a view function of a blueprint or a rendered
template and you want to link to another endpoint of the same blueprint,
you can use relative redirects by prefixing the endpoint with a dot only::

    url_for('.index')

This will link to ``admin.index`` for instance in case the current request
was dispatched to any other admin blueprint endpoint.
