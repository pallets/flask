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

Blueprints instead provide separation at the Flask level, share
application config, and can change an application object as necessary with
being registered. The downside is that you cannot unregister a blueprint
once an application was created without having to destroy the whole
application object.

The Concept of Blueprints
-------------------------

The basic concept of blueprints is that they record operations to execute
when registered on an application.  Flask associates view functions with
blueprints when dispatching requests and generating URLs from one endpoint
to another.

My First Blueprint
------------------

This is what a very basic blueprint looks like.  In this case we want to
implement a blueprint that does simple rendering of static templates::

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

When you bind a function with the help of the ``@simple_page.route``
decorator the blueprint will record the intention of registering the
function `show` on the application when it's later registered.
Additionally it will prefix the endpoint of the function with the
name of the blueprint which was given to the :class:`Blueprint`
constructor (in this case also ``simple_page``).

Registering Blueprints
----------------------

So how do you register that blueprint?  Like this::

    from flask import Flask
    from yourapplication.simple_page import simple_page

    app = Flask(__name__)
    app.register_blueprint(simple_page)

If you check the rules registered on the application, you will find
these::

    [<Rule '/static/<filename>' (HEAD, OPTIONS, GET) -> static>,
     <Rule '/<page>' (HEAD, OPTIONS, GET) -> simple_page.show>,
     <Rule '/' (HEAD, OPTIONS, GET) -> simple_page.show>]

The first one is obviously from the application ifself for the static
files.  The other two are for the `show` function of the ``simple_page``
blueprint.  As you can see, they are also prefixed with the name of the
blueprint and separated by a dot (``.``).

Blueprints however can also be mounted at different locations::

    app.register_blueprint(simple_page, url_prefix='/pages')

And sure enough, these are the generated rules::

    [<Rule '/static/<filename>' (HEAD, OPTIONS, GET) -> static>,
     <Rule '/pages/<page>' (HEAD, OPTIONS, GET) -> simple_page.show>,
     <Rule '/pages/' (HEAD, OPTIONS, GET) -> simple_page.show>]

On top of that you can register blueprints multiple times though not every
blueprint might respond properly to that.  In fact it depends on how the
blueprint is implemented if it can be mounted more than once.

Blueprint Resources
-------------------

Blueprints can provide resources as well.  Sometimes you might want to
introduce a blueprint only for the resources it provides.

Blueprint Resource Folder
`````````````````````````

Like for regular applications, blueprints are considered to be contained
in a folder.  While multiple blueprints can originate from the same folder,
it does not have to be the case and it's usually not recommended.

The folder is inferred from the second argument to :class:`Blueprint` which
is usually `__name__`.  This argument specifies what logical Python
module or package corresponds to the blueprint.  If it points to an actual
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
