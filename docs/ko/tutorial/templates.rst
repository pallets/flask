.. _tutorial-templates:

스텝 6: 템플릿
=====================

이제 우리는 템플릿을 작업해야 한다. 만약 우리가 지금까지 만든 flaskr에 
URL을 요청하는 경우 Flask는 템플릿(templates)을 찾을 수 없다는 예외를 발생시킬것이다.
템플릿들은 `Jinja2`_ 문법을 사용하고 있고 autoescaping 가 기본으로 활성화되있다.
이 의미는 개발자가 직접 :class"`~flask.Markup` 이나 혹은 ``|safe`` 필터를 템플릿에서
직접 관리하지 않아도 된다는 뜻이다.
Jinja2는 ``<`` 혹은 ``>`` 와 같은 특별한 문자들에 대하여 XML에서 표기하는 동등한 표기법으로
탈피할 수 있도록 보장한다.

우리는 또한 가능한 모든 페이지에서 웹 사이트의 레이아웃을 재사용 할 수있도록 템플릿 상속을 
할 수 있도록 하고 있다.


다음의 템플릿을 `templates` 폴더에 넣도록 하자:

.. _Jinja2: http://jinja.pocoo.org/2/documentation/templates


layout.html
-----------

이 템플릿은 HTML의 뼈대(skeleton)을, 헤더 및 로그인링크 (혹은 사용자가 로그인
한 경우에는 로그아웃 링크)들을 포함하고 있다. 또한 상황에 딸라 메시지를 보여주기도 한다.
부모 템플릿의 ``{% block body %}`` 블럭은 이를 상속받은 후손 템플릿에서 동일한 이름의 블럭위치에
치환된다.

:class:`~flask.session` dict 객체도 템플릿안에서 사용 가능할 수 있으며 이를 이용해
사용자가 로그인되어 있는지 그렇지 않은지 확인 할 수 있다. 

Jinja에서는 세션에서 키(key)가 없는 경우에도 제공된 dict 객체의 누락된 속성값이나 객체에 
접근이 가능하다. 세션곅체에  ``'logged_in'`` 키가 없는 경우에도 가능하다.


.. sourcecode:: html+jinja

    <!doctype html>
    <title>Flaskr</title>
    <link rel=stylesheet type=text/css href="{{ url_for('static', filename='style.css') }}">
    <div class=page>
      <h1>Flaskr</h1>
      <div class=metanav>
      {% if not session.logged_in %}
        <a href="{{ url_for('login') }}">log in</a>
      {% else %}
        <a href="{{ url_for('logout') }}">log out</a>
      {% endif %}
      </div>
      {% for message in get_flashed_messages() %}
        <div class=flash>{{ message }}</div>
      {% endfor %}
      {% block body %}{% endblock %}
    </div>

show_entries.html
-----------------

이 템플릿은 `layout.html` 템플릿을 상속받는 메시지를 보여주는 템플릿이다.
유의할 점은 `for` 루프는 우리가 :func:`~flask.render_template` 함수에서
전달한 메시지에들 만큼 반복된다는 점이다.
우리는 또한 form이 전송될때 `add_entry` 함수가 `HTTP`의 `POST` 메소드를 통해서 
전송된다는 것을 이야기 해둔다.:

.. sourcecode:: html+jinja

    {% extends "layout.html" %}
    {% block body %}
      {% if session.logged_in %}
        <form action="{{ url_for('add_entry') }}" method=post class=add-entry>
          <dl>
            <dt>Title:
            <dd><input type=text size=30 name=title>
            <dt>Text:
            <dd><textarea name=text rows=5 cols=40></textarea>
            <dd><input type=submit value=Share>
          </dl>
        </form>
      {% endif %}
      <ul class=entries>
      {% for entry in entries %}
        <li><h2>{{ entry.title }}</h2>{{ entry.text|safe }}
      {% else %}
        <li><em>Unbelievable.  No entries here so far</em>
      {% endfor %}
      </ul>
    {% endblock %}

login.html
----------

마지막으로 로그인 템플릿은 기본적으로 사용자가 로그인을 할 수 있도록 보여주는 form 이다. :

.. sourcecode:: html+jinja

    {% extends "layout.html" %}
    {% block body %}
      <h2>Login</h2>
      {% if error %}<p class=error><strong>Error:</strong> {{ error }}{% endif %}
      <form action="{{ url_for('login') }}" method=post>
        <dl>
          <dt>Username:
          <dd><input type=text name=username>
          <dt>Password:
          <dd><input type=password name=password>
          <dd><input type=submit value=Login>
        </dl>
      </form>
    {% endblock %}

다음 섹션에서 계속 :ref:`tutorial-css`.
