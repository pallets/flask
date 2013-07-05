.. _template-inheritance:

템플릿 상속
===========

진자(Jinja)의 가장 강력한 부분은 템플릿 상속 기능이다.  템플릿 상속은 여러분의 사이트에
대한 모든 일반적인 요소들을 포함한 기본 "스켈레톤(skeleton)" 템플릿을 생성하도록 하고
자식 템플릿은 기본 템플릿을 오버라이드(override)할 수 있는 **blocks** 을 정의한다.

복잡해 보이지만 꽤 간단하다.  예제로 시작하는게 이해하는데 가장 쉽다.


기본 템플릿
-----------

우리가 ``layout.html`` 이라 부를 이 팀플릿은 간단한 두개의 칼럼을 가진 페이지로
사용할 간단한 HTML 스켈레톤 문서를 정의한다.  내용의 빈 블럭을 채우것이 "자식"
템플릿의 일이다:

.. sourcecode:: html+jinja

    <!doctype html>
    <html>
      <head>
        {% block head %}
        <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
        <title>{% block title %}{% endblock %} - My Webpage</title>
        {% endblock %}
      </head>
    <body>
      <div id="content">{% block content %}{% endblock %}</div>
      <div id="footer">
        {% block footer %}
        &copy; Copyright 2010 by <a href="http://domain.invalid/">you</a>.
        {% endblock %}
      </div>
    </body>

이 예제에서, ``{% block %}`` 태그는 자식 템플릿이 채울 수 있는 네개의 블럭을
정의한다. `block` 태그가 하는 전부는 템플릿 엔진에 자식 템플릿이 템플릿의 `block`
태그를 오버라이드할 수 도 있다라고 알려준다.

자식 템플릿
-----------

자식 템플릿은 아래와 같이 보일 수도 있다:

.. sourcecode:: html+jinja

    {% extends "layout.html" %}
    {% block title %}Index{% endblock %}
    {% block head %}
      {{ super() }}
      <style type="text/css">
        .important { color: #336699; }
      </style>
    {% endblock %}
    {% block content %}
      <h1>Index</h1>
      <p class="important">
        Welcome on my awesome homepage.
    {% endblock %}

``{% extends %}`` 태그가 여기서 핵심이다.  이 태그는 템플릿 엔진에게 이 템플릿이
다른 템플릿을 "확장(extends)" 한다라고 알려준다.  템플릿 시스템이 이 템플릿을 
검증할 때, 가장 먼저 부모 템플릿을 찾는다.  그 확장 태그가 템플릿에서 가장 먼저
있어야 한다.  부모 템플릿에 정의된 블럭의 내용을 보여주려면 ``{{ super() }}`` 를
사용하면 된다.
