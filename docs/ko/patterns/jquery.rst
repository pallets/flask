AJAX with jQuery
================

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


JSON View Functions
-------------------

Now let's create a server side function that accepts two URL arguments of
numbers which should be added together and then sent back to the
application in a JSON object.  This is a really ridiculous example and is
something you usually would do on the client side alone, but a simple
example that shows how you would use jQuery and Flask nonetheless::

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

As you can see I also added an `index` method here that renders a
template.  This template will load jQuery as above and have a little form
we can add two numbers and a link to trigger the function on the server
side.

Note that we are using the :meth:`~werkzeug.datastructures.MultiDict.get` method here
which will never fail.  If the key is missing a default value (here ``0``)
is returned.  Furthermore it can convert values to a specific type (like
in our case `int`).  This is especially handy for code that is
triggered by a script (APIs, JavaScript etc.) because you don't need
special error reporting in that case.

The HTML
--------

Your index.html template either has to extend a `layout.html` template with
jQuery loaded and the `$SCRIPT_ROOT` variable set, or do that on the top.
Here's the HTML code needed for our little application (`index.html`).
Notice that we also drop the script directly into the HTML here.  It is
usually a better idea to have that in a separate script file:

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

I won't got into detail here about how jQuery works, just a very quick
explanation of the little bit of code above:

1. ``$(function() { ... })`` specifies code that should run once the
   browser is done loading the basic parts of the page.
2. ``$('selector')`` selects an element and lets you operate on it.
3. ``element.bind('event', func)`` specifies a function that should run
   when the user clicked on the element.  If that function returns
   `false`, the default behavior will not kick in (in this case, navigate
   to the `#` URL).
4. ``$.getJSON(url, data, func)`` sends a `GET` request to `url` and will
   send the contents of the `data` object as query parameters.  Once the
   data arrived, it will call the given function with the return value as
   argument.  Note that we can use the `$SCRIPT_ROOT` variable here that
   we set earlier.

If you don't get the whole picture, download the `sourcecode
for this example
<http://github.com/mitsuhiko/flask/tree/master/examples/jqueryexample>`_
from github.
