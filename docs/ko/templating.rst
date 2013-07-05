템플릿
=========

Flask는 템플릿엔진으로 Jinja2를 사용한다. 물론 다른 무료 템플릿엔진을 
사용할 수 있지만, Flask를 구동하기 위해서는 Jinja2를 반드시 설치해야 한다. 
Jinja2가 필요한 이유는 Flask의 풍부한 기능 확장을 위해서이다. 
확장기능은 Jinja2와 의존관계에 있을 수도 있다.

이 섹션은 Jinja2가 Flask에 어떻게 통합되어 있는지 빠르게 소개하는 섹션이다.
만약 템플릿엔진 자체의 문법에 대한 정보를 얻기 원한다면 Jinja2 공식 문서인 `Jinja2 Template
Documentation <http://jinja.pocoo.org/2/documentation/templates>`_  를 참고하라.


Jinja 설정
-----------

사용자가 임의로 설정하지 않는이상, Jinja2는 다음과 같이 Flask에 의해 설정되어 있다.:

-   자동변환(autoescaping) 기능은 ``.html`` , ``.xml`` 과 ``.xhtml`` 과 같은 모든 
    템플릿 파일들에 대해서 기본으로 활성화되어 있다.  
-   하나의 템플릿은 in/out에 대한 자동변환(autoescape) 기능을 ``{% autoescape %}`` 태그를 이용하여 사용할 수 있다.
-   Flask는 기본적으로 Jinja2 컨텍스트(context)를 통해서 전역 함수들과 헬퍼함수들을 제공한다.


표준 컨텍스트
----------------

다음의 전역 변수들은 Jinja2에서 기본으로 사용가능하다.:

.. data:: config
   :noindex:

   현재 설정값을 가지고 있는 객체 (:data:`flask.config`)

   .. versionadded:: 0.6

   .. versionchanged:: 0.10
      This is now always available, even in imported templates.

.. data:: request
   :noindex:

   현재 요청된 객체 (request object)  (:class:`flask.request`). 이 변수는 
   템플릿이 활성화된 컨텍스트에서 요청된것이 아니라면 유효하지 않다.

.. data:: session
   :noindex:

   현재 가지고 있는 세션 객체 (:class:`flask.session`).  이 변수는 
   템플릿이 활성화된 컨텍스트에서 요청된것이 아니라면 유효하지 않다.

.. data:: g
   :noindex:

   요청(request)에 한정되어진 전역 변수  (:data:`flask.g`) . 이 변수는 
   템플릿이 활성화된 컨텍스트에서 요청된것이 아니라면 유효하지 않다.

.. function:: url_for
   :noindex:

   :func:`flask.url_for` 함수 참고.

.. function:: get_flashed_messages
   :noindex:

   :func:`flask.get_flashed_messages` 함수 참고.

.. admonition:: Jinja 환경에서의 작동방식

   이러한 변수들은 변수 컨텍스트에 추가되며 전역 변수가 아니다.
   전역변수와의 차이점은 컨텍스트에서 불려진 템플릿에서는 기본적으로 보이지는 않는다는 것이다.
   이것은 일부분은 성능을 고려하기위해서고 일부분은 명시적으로 유지하기 위해서이다.

   이것은 무엇을 의미하는가? 만약 불러오고 싶은 매크로(macro)를 가지고 있다면,
   요청 객체(request object)에 접근하는 것이 필요하며 여기에 두가지 가능성이 있다.: 

   1.   매크로(macro)로 요청 객체를 파라미터로 명시적으로 전달하거나,
        관심있는 객체에 속성값으로 가지고 있어야 한다.
   2.   매크로를 컨텍스트로 불러와야한다.

   다음과 같이 컨텍스트에서 불러온다.:

   .. sourcecode:: jinja

      {% from '_helpers.html' import my_macro with context %}


표준 필터
----------------

다음 필터들은 Jinja2에서 자체적으로 추가 제공되어 이용할 수 있는 것들이다.:

.. function:: tojson
   :noindex:
   
   이 기능은 JSON 표기법으로 주어진 객체를 변환기켜주는 것이다.
   예를들어 만약 JavaScript를 즉석에서 생성하려고 한다면 이기능은 많은 도움이 될것이다.
   
   `script` 태그안에서는 변환(escaping)이 반드시 일어나서는 안되기 때문에,
   ``|safe`` 필터가 `script` 태그안에서 비활성화되도록 보장해야 한다.:

   .. sourcecode:: html+jinja

       <script type=text/javascript>
           doSomethingWith({{ user.username|tojson|safe }});
       </script>
   
   ``|tojson`` 필터는 올바르게 슬래쉬들을 변환해 준다.


자동변환(Autoescaping) 제어하기
------------------------

자동변환(Autoescaping)은 자동으로 특수 문자들을 변환시켜주는 개념이다.
특수문자들은 HTML (혹은 XML, 그리고 XHTML) 문서 에서 ``&``, ``>``, ``<``, ``"`` , ``'`` 
에 해당한다. 이 문자들은 해당 문서에서 특별한 의미들을 담고 있고 이 문자들을 
텍스트 그대로 사용하고 싶다면 "entities" 라고 불리우는 값들로 변환하여야 한다. 
이렇게 하지 않으면 본문에 해당 문자들을 사용할 수 없어 사용자에게 불만을 
초래할뿐만 아니라 보안 문제도 발생할 수 있다.
(다음을 참고 :ref:`xss`)

그러나 때때로 템플릿에서 이러한 자동변환을 비활성화 할 필요가 있다. 
만약 명시적으로 HTML을 페이지에 삽입하려고 한다면,  예를 들어 HTML로 전환되는 
마크다운(markdown)과 같은 안전한 HTML을 생성하는 특정 시스템으로부터 오는
것일 경우에는 유용하다.

이 경우 세가지 방법이 있다:

-   Python 코드에서는, HTML 문자열을 :class:`~flask.Markup` 객체를 통해서
    템플릿에 전달되기 전에 래핑한다. 이방법은 일반적으로 권장되는 방법이다.
-   템플릿 내부에, ``|safe`` 필터를 명시적으로 사용하여 문자열을 안전한 HTML이 
    되도록 한다. (``{{ myvariable|safe }}``)
-   일시적으로 모두 자동변환(autoescape) 시스템을 해제한다.

템플릿에서 자동변환(autoescape) 시스템을 비활성화 하려면, ``{%autoescape %}``
블럭을 이용할 수 있다. :

.. sourcecode:: html+jinja

    {% autoescape false %}
        <p>autoescaping is disabled here
        <p>{{ will_not_be_escaped }}
    {% endautoescape %}

이 블럭이 수행될때마다, 이 블록에서 사용하는 변수애 대해 각별한 주의를 기울여야 한다.

.. _registering-filters:


필터 등록하기
-------------------

만약 Jinja2에서 자신만의 필터를 직접 등록하기를 원한다면 두가지 방법이있다.
다음의 방법을 이용할 수 있다.
:attr:`~flask.Flask.jinja_env` Jinja 어플리케이션에서 이용하거나
:meth:`~flask.Flask.template_filter` 데코레이터(decorator)를 이용가능하다.

다음 두개의 예제는 객체의 값을 거꾸로 만드는 같은 일을 한다::

    @app.template_filter('reverse')
    def reverse_filter(s):
        return s[::-1]

    def reverse_filter(s):
        return s[::-1]
    app.jinja_env.filters['reverse'] = reverse_filter

만약 함수이름을 필터이름으로 사용하려면 데코레이터(decorator)의 아규먼트는 선택조건이어야한다.
한번 필터가 등록되면, Jinja2의 내장 필터를 사용하는 것과 똑같이 사용이 가능하다, 
예를 들면 만약 `mylist` 라는 Python 리스트(list)가 컨텍스트에 있다면  ::

    {% for x in mylist | reverse %}
    {% endfor %}


컨텍스트 프로세서(context processor)
------------------

새로운 변수들을 자동으로 템플릿의 컨텍스트에 주입시키기 위해서 
Flask에는 컨텍스트 프로세서들이 존재한다.
컨텍스트 프로세서들은 새로운 값들을 템플릿 컨텍스트에 주입시키기 위해
템플릿이 렌더링되기 전에 실행되어야 한다. 
템플릿 프로세서는 딕셔너리(dictionary) 객체를 리턴하는 함수이다.
이 딕셔너리의 키와 밸류들은 어플리케이션에서의 모든 템플릿들을 위해서 
템플릿 컨텍스트에 통합된다.::

    @app.context_processor
    def inject_user():
        return dict(user=g.user)

위의 컨텍스트 프로세서는 `user` 라고 부르는 유효한 변수를 템플릿 내부에
`g.user` 의 값으로 만든다. 이 예제는 `g` 변수가 템플릿에서 유효하기 때문에 
그렇게 흥미롭지는 않지만 어떻게 동작하는지에 대한 아이디어를 제공한다.

변수들은 값들에 제한되지 않으며, 또한 컨텍스트 프로세서는 템플릿에서
함수들을 사용할 수 있도록 해준다. 
(Python이 패싱 어라운드(passing around)함수를 지원하기 때문에)::

    @app.context_processor
    def utility_processor():
        def format_price(amount, currency=u'€'):
            return u'{0:.2f}{1}'.format(amount, currency)
        return dict(format_price=format_price)

위의 컨텍스트 프로세서는 `format_price` 함수를 모든 템플릿들에서 사용가능하도록 해준다 ::

    {{ format_price(0.33) }}

또한 `format_price` 를 템플릿 필터로 만들 수도 있다. (다음을 참고 
:ref:`registering-filters`), 하지만 이 예제에서는 컨텍스트 프로세서에 어떻게 함수들을
전달하는지에 대해서만 설명한다.
