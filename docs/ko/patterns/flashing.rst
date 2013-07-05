.. _message-flashing-pattern:

메시지 플래싱(Message Flashing)
===============================

좋은 어플리케이션과 사용자 인터페이스의 모든것은 피드백이다.  사용자가 
충분한 피드백을 얻지 못한다면 그들은 결국 그 어플리케이션을 싫어할 것이다.
플라스크는 플래싱 시스템을 가지고 사용자에게 피드백을 주는 정말 간단한
방법을 제공한다.  플래싱 시스템은 기본적으로 요청의 끝에 메시지를 기록하고
그 다음 요청에서만 그 메시지에 접근할 수 있게 한다.  보통은 플래싱을 처리하는
레이아웃 템플릿과 결함되어 사용된다.

간단한 플래싱
-------------

그래서 아래 전체 예제를 준비했다::

    from flask import Flask, flash, redirect, render_template, \
         request, url_for

    app = Flask(__name__)
    app.secret_key = 'some_secret'

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        error = None
        if request.method == 'POST':
            if request.form['username'] != 'admin' or \
                    request.form['password'] != 'secret':
                error = 'Invalid credentials'
            else:
                flash('You were successfully logged in')
                return redirect(url_for('index'))
        return render_template('login.html', error=error)

    if __name__ == "__main__":
        app.run()


그리고 여기에 그 마법을 다룰 ``layout.html`` 템플릿이 있다:

.. sourcecode:: html+jinja

   <!doctype html>
   <title>My Application</title>
   {% with messages = get_flashed_messages() %}
     {% if messages %}
       <ul class=flashes>
       {% for message in messages %}
         <li>{{ message }}</li>
       {% endfor %}
       </ul>
     {% endif %}
   {% endwith %}
   {% block body %}{% endblock %}

이것은 index.html 템플릿이다:

.. sourcecode:: html+jinja

   {% extends "layout.html" %}
   {% block body %}
     <h1>Overview</h1>
     <p>Do you want to <a href="{{ url_for('login') }}">log in?</a>
   {% endblock %}

물론 로그인 템플릿도 있다:

.. sourcecode:: html+jinja

   {% extends "layout.html" %}
   {% block body %}
     <h1>Login</h1>
     {% if error %}
       <p class=error><strong>Error:</strong> {{ error }}
     {% endif %}
     <form action="" method=post>
       <dl>
         <dt>Username:
         <dd><input type=text name=username value="{{
             request.form.username }}">
         <dt>Password:
         <dd><input type=password name=password>
       </dl>
       <p><input type=submit value=Login>
     </form>
   {% endblock %}

카테고리를 가진 플래싱
------------------

.. versionadded:: 0.3

메시지를 플래싱 할 때 카테고리를 제공하는 것 또한 가능하다.  어떤 것도 
제공되지 않는다면 기본 카테고리는 ``'message'`` 이다.  다른 카테고리도
사용자에게 더 좋은 피드백을 제공하는데 사용될 수 있다.  예를 들면, 오류
메시지는 붉은색 뒷배경으로 표시될 수 있다.

다른 카테고리로 메시지를 플래시하기 위해, :func:`~flask.flash` function::
의 두번째 인자로 카테고리를 넘겨주면 된다.

    flash(u'Invalid password provided', 'error')

그리고 나서 템플릿 안에서 그 카테고리를 받으려면 
:func:`~flask.get_flashed_messages` 함수를 사용해야한다. 아래의 루프는 
그러한 상황에서 약간 다르게 보인다:

.. sourcecode:: html+jinja

   {% with messages = get_flashed_messages(with_categories=true) %}
     {% if messages %}
       <ul class=flashes>
       {% for category, message in messages %}
         <li class="{{ category }}">{{ message }}</li>
       {% endfor %}
       </ul>
     {% endif %}
   {% endwith %}

이것이 플래시 메시지를 보여주는 방법의 한가지 예이다.  메시지에 
``<strong>Error:</strong>`` 과 같은 접두어를 더하기 위해 카테고리를 
또한 사용할 수 도 있다.

플래시 메시지를 필터링하기
--------------------------

.. versionadded:: 0.9

선택적으로 여러분은 :func:`~flask.get_flashed_messages` 의 결과를 필터링할 
카테고리의 목록을 넘겨줄 수 있다.  여러분이 분리된 블럭에 각 카테고리를
보여주고 싶다면 이 기능은 유용하다.

.. sourcecode:: html+jinja

    {% with errors = get_flashed_messages(category_filter=["error"]) %}
    {% if errors %}
    <div class="alert-message block-message error">
      <a class="close" href="#">×</a>
      <ul>
        {%- for msg in errors %}
        <li>{{ msg }}</li>
        {% endfor -%}
      </ul>
    </div>
    {% endif %}
    {% endwith %}
