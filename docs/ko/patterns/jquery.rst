jQuery로  AJAX 처리하기
=======================

`jQuery`_ 는 DOM과 자바스크립트에 공통으로 사용되어 작업을 간편하게 
해주는데 사용되는 작은 자바스크립트 라이브러리이다.  jQuery는 또한 
서버와 클라이언트 사이에 JSON으로 통신하며 더 동적인 웹 어플리케이션을 
만들게 해주는 최상의 도구이다. 

JSON 그 자체는 매우 경량의 전송 포맷으로, 널리 지원되며 굉장히 파싱하기
쉬운 파이썬 기본 타입(numbers,strings, dicts와 lists)과 유사하게 생겼다.
그것은 수년전에 널리 사용되었고 웹 어플리케이션에서 전송포맷으로 XML을
빠르게 대체하고 있다.

여러분이 파이썬 2.6을 갖고 있다면 JSON은 그 패키지에서 사용될 것이고,
파이썬 2.5에서는 PyPI에서 `simplejson`_ 라이브러리를 설치해야할 것이다.

.. _jQuery: http://jquery.com/
.. _simplejson: http://pypi.python.org/pypi/simplejson

jQuery 로딩하기
---------------

jQuery를 사용하기 위해서, 먼저 그것을 다운로드받고 여러분 어플리케이션의
static 폴더에 그 파일을 넣어야한다. 그리고 나서 그것이 로드되는지 확인한다.
이상적으로 여러분은 모든 페이지에서 사용할 layout 템플릿을 갖고 거기에서 
`<body>` 의 하단에 jQuery를 로드할 스크립트 문을 추가해야한다:

.. sourcecode:: html

   <script type=text/javascript src="{{
     url_for('static', filename='jquery.js') }}"></script>

다른 방법은 구글의 `AJAX Libraries API
<http://code.google.com/apis/ajaxlibs/documentation/>`_ 를 사용하는 것이다:

.. sourcecode:: html

    <script src="//ajax.googleapis.com/ajax/libs/jquery/1.6.1/jquery.js"></script>
    <script>window.jQuery || document.write('<script src="{{
      url_for('static', filename='jquery.js') }}">\x3C/script>')</script>

이 경우에 여러분은 대비책으로 static 폴더에 jQuery를 넣어둬야 하지만, 우선
구글로 부터 직접 그 라이브러리를 로딩하도록 할 것이다.  이것은 사용자들이
구글에서 같은 jQuery 버전을 사용하는 다른 웹사이트를 적어도 한번 방문했다면
여러분의 웹 사이트는 더 빠르게 로딩될 것이라는 점에서 장점이 있다. 왜냐하면
그 라이브러리는 브라우저 캐쉬에 이미 있을 것이기 때문이다.

내 사이트는 어디에 있는가?
--------------------------

여러분의 어플리케이션이 어디에 있는지 알고 있는가?  여러분이 개발하고 있다면
그 답은 굉장히 간단하다:  로컬호스트의 어떤 포트와 직접적으로 그 서버의 루트에
있다.  그러나 여러분이 최근에 어플리케이션을 다른 위치로 이동하기로 결정했다면
어떠한가?  예를 들면 ``http://example.com/myapp`` 과 같은 사이트로 말이다.
서버 측면에서 이것은 어떤 문제도 되지 않는데 왜냐하면 우리는 그 질문에 
답변할 수 있는 간편한 :func:`~flask.url_for` 함수를 사용하고 있기 때문이다.
하지만, 우리는 jQuery를 사용하고 있고 어플리케이션에 경로를 하드코딩하지 
않아야 하고 그것을 동적으로 만들어야 한다. 그렇다면 어떻게 해야겠는가?

간단한 방법은 어플리케이션의 루트에 대한 접두어에 전역 변수를 설정한 페이지에
스크립트 태그를 추가하는 것이다. 다음과 같다:

.. sourcecode:: html+jinja

   <script type=text/javascript>
     $SCRIPT_ROOT = {{ request.script_root|tojson|safe }};
   </script>

``|safe`` 는 진자가 HTML 규칙을 가진 JSON 인코딩된 문자열을 이스케이핑하지
못하게 하기 위해 필요하다.  보통은 이것이 필요하겠지만, 다른 규칙을 적용하는 
`script` 블럭 안에 두겠다.

.. admonition:: Information for Pros

   HTML에서 `script` 태그는 엔티티로 분석되지 않는 `CDATA` 로 선언된다.
   ``</script>`` 까지 모든 것은 스크립트로 처리된다. 이것은 또한 ``</`` 와
   script 태그 사이의 어떤것도 존재해서는 안된다는 것을 의미한다.  
   ``|tojson`` 은 여기서 제대로 적용되어 이스케이핑 슬래쉬도 잘 처리된다
   (``{{ "</script>"|tojson|safe }}`` 은 ``"<\/script>"`` 게 보인다).


JSON 뷰 함수
------------

이제 두개의 URL 인자를 받아서 더하고 그 결과를 JSON 객체로 어플리케이션에
되돌려주는 서버 측 함수를 생성하자.  이것은 정말 우스운 예제이고 보통은
클라이언트 측에서만 동작할 내용이지만, 그럼에도 불구하고  jQuery와 플라스크가 
동작하는 방식을 보여주는 예제이다::

    from flask import Flask, jsonify, render_template, request
    app = Flask(__name__)

    @app.route('/_add_numbers')
    def add_numbers():
        a = request.args.get('a', 0, type=int)
        b = request.args.get('b', 0, type=int)
        return jsonify(result=a + b)

    @app.route('/')
    def index():
        return render_template('index.html')

여러분이 볼 수 있는 것처럼 템플릿을 뿌려주는 `index` 메소드를 추가했다.
이 템플릿은 위에서 처럼 jQuery를 로딩할 것이고 두 숫자를 더할 수 있는 
작은 폼과 서버 측에서 호출될 함수에 대한 링크를 갖고 있다.

우리는 여기서 절대 실패하지 않을 :meth:`~werkzeug.datastructures.MultiDict.get`
메소드를 사용하고 있다는 점에 주목하라.  키가 없다면 기본값 (여기서는 ``0``) 이
반환된다는 것이다.  게다가 그것은 값을 특정 타입 (여기서는 `int`)으로 변환할
수 있다.  이것은 특히나 스크립트 (APIs, 자바스크립트 등) 로 실행되는 코드에 특히나
유용한데 왜냐하면 여러분은 키가 없을 때 발생하는 특별한 오류 보고가 필요없기 
때문이다.

HTML
----

위의 index.html 템플릿은 jQuery를 로딩하고 `$SCRIPT_ROOT` 변수를 설정하면서
`layout.html` 템플릿을 확장하거나 제일 상위에 그것을 설정해야한다.
여기에 우리의 작은 어플리케이션에 대해 필요한 HTML 코드가 있다 (`index.html`).
우리는 또한 필요한 스크립트를 바로 HTML에 넣는다는 것에 주목해라. 분리된 
스크립트 파일에 그 코드를 갖는게 일반적으로는 더 나은 방식이다:

.. sourcecode:: html

    <script type=text/javascript>
      $(function() {
        $('a#calculate').bind('click', function() {
          $.getJSON($SCRIPT_ROOT + '/_add_numbers', {
            a: $('input[name="a"]').val(),
            b: $('input[name="b"]').val()
          }, function(data) {
            $("#result").text(data.result);
          });
          return false;
        });
      });
    </script>
    <h1>jQuery Example</h1>
    <p><input type=text size=5 name=a> +
       <input type=text size=5 name=b> =
       <span id=result>?</span>
    <p><a href=# id=calculate>calculate server side</a>

여기서는 jQuery가 어떠헥 동작하는지 자세하게 들어가지는 않을 것이고,
단지 위에 있는 일부 코드에 대한 간략한 설명만 있을 것이다:

1. ``$(function() { ... })`` 는 브라우저가 해당 페이지의 기본 구성들을 
   로딩할 때 실행될 코드를 지정한다.
2. ``$('selector')`` 는 요소를 선택하고 그 요소에서 실행하게 한다.
3. ``element.bind('event', func)`` 는 사용자가 해당 요소에서 클릭했을 때
   실행될 함수를 지정한다.  그 함수가 `false` 를 반환하면, 기본 동작은 
   시작되지 않을 것이다 (이 경우, `#` URL로 이동).
4. ``$.getJSON(url, data, func)`` 은 `url` 로 `GET` 요청을 보내고 쿼리 인자로
   `data` 객체의 내요을 보낼 것이다.  일단 데이터가 도착하면, 인자로 반환 값을
   가지고 주어진 함수를 호출할 것이다. 여기서는 앞에서 설정한 `$SCRIPT_ROOT` 
   변수를 사용할 수 있다는 것에 주목해라.

여러분이 전체적으로 이해가 안된다면, 깃허브(github)에서 이 예제에 대한 
`소스 코드
<http://github.com/mitsuhiko/flask/tree/master/examples/jqueryexample>`_.
