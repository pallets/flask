WTForms를 가지고 폼 유효성 확인하기
===================================

여러분이 브라우저에서 전송되는 폼 데이타를 가지고 작업해야할 때
곧 뷰 코드는 읽기가 매우 어려워진다.  이 과정을 더 쉽게 관리할 수 있도록
설계된 라이브러리들이 있다.  그것들 중 하나가 우리가 여기서 다룰 예정인
`WTForms`_  이다.  여러분이 많은 폼을 갖는 상황에 있다면, 이것을 한번
시도해보길 원할지도 모른다.

여러분이 WTForms로 작업하고 있을 때 여러분은 먼저 클래스로 그 폼들을
정의해야한다.  어플리케이션을 여러 모듈로 쪼개고 (:ref:`larger-applications`)
폼에 대한 분리된 모듈을 추가하는 것을 권고한다.

.. admonition:: 확장을 가지고 대부분의 WTForms 얻기

   `Flask-WTF`_ 확장은 이 패턴을 확대하고 폼과 작업하면서 플라스크를 더
   재밌게 만드는 몇가지 유효한 작은 헬퍼들을 추가한다.  여러분은 `PyPI
   <http://pypi.python.org/pypi/Flask-WTF>`_ 에서 그 확장을 얻을 수 있다.

.. _Flask-WTF: http://packages.python.org/Flask-WTF/

폼(Forms)
---------

이것은 전형적인 등록 페이지에 대한 예제 폼이다::

    from wtforms import Form, BooleanField, TextField, PasswordField, validators

    class RegistrationForm(Form):
        username = TextField('Username', [validators.Length(min=4, max=25)])
        email = TextField('Email Address', [validators.Length(min=6, max=35)])
        password = PasswordField('New Password', [
            validators.Required(),
            validators.EqualTo('confirm', message='Passwords must match')
        ])
        confirm = PasswordField('Repeat Password')
        accept_tos = BooleanField('I accept the TOS', [validators.Required()])

뷰 안에서(In the View)
----------------------

뷰 함수에서, 이 폼의 사용은 이것 처럼 보인다::

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        form = RegistrationForm(request.form)
        if request.method == 'POST' and form.validate():
            user = User(form.username.data, form.email.data,
                        form.password.data)
            db_session.add(user)
            flash('Thanks for registering')
            return redirect(url_for('login'))
        return render_template('register.html', form=form)


뷰가 SQLAlchemy (:ref:`sqlalchemy-pattern`) 를 사용한다고 가정하지만, 
물론 필수조건은 아니라는 사실을 염두해라. 필요에 따라 코드를 수정해라.

기억할 것 :

1. HTTP `POST` 메소드로 데이터가 전송됐다면 요청의 :attr:`~flask.request.form`
   값으로 부터 폼을 생성하고 `GET` 으로 전송됐다면 :attr:`~flask.request.args`
   에서 폼을 생성한다.
2. 데이터를 검증하기 위해서, :func:`~wtforms.form.Form.validate` 메소드
   를 호출하고 데이터가 유효하면 `True`를 얻고 유효하지 않으면 `False`를
   얻을 것이다.
3. 폼에서 개별 값에 접근하기 위해서, `form.<NAME>.data` 으로 접근한다.

템플릿에 있는 폼
----------------

이제 템플릿 측면에서 살펴보자.  여러분이 템플릿에 폼을 넘겨주면 그 폼을
템플릿에서 쉽게 뿌려줄 수 있다.  이런 방식이 얼마나 쉽게 되는지 보기 위해
다음 템플릿 예제를 보자.  WTForms 가 이미 폼 생성의 반을 처리했다.  조금 더 
멋지게 만들기 위해서, 우리는 레이블과 오류가 발생한다면 오류의 목록까지 가진
필드를 그려줄 매크로(macro)를 작성할 수 있다.

여기 그런 방식의 메크로를 가진 예제인 `_formhelpers.html` 템플릿이 있다:

.. sourcecode:: html+jinja

    {% macro render_field(field) %}
      <dt>{{ field.label }}
      <dd>{{ field(**kwargs)|safe }}
      {% if field.errors %}
        <ul class=errors>
        {% for error in field.errors %}
          <li>{{ error }}</li>
        {% endfor %}
        </ul>
      {% endif %}
      </dd>
    {% endmacro %}

이 매크로는 필드를 뿌리는 WTForm의 필드 함수로 넘겨지는 몇가지 키워드 
인자를 허용한다.  그 키워드 인자는 HTML 속성으로 추가될 것이다.  그래서
예를 들면 여러분은 입력 요소에 클래스(class)를 추가하기 위해 
``render_field(form.username, class='username')`` 를 호출할 수 있다.
WTForms는 표준 파이썬 유니코드 문자열을 반환하므로 우리는 진자2(Jinja2)에
`|safe` 필터를 가지고 이 데이터를 이미 HTML 이스케이프처리 하게 해야한다
는 것에 주목해라.

아래는 `_formhelpers.html` 템플릿을 이용해서 위에서 사용된 함수로 만든
`register.html` 템플릿이다:

.. sourcecode:: html+jinja

    {% from "_formhelpers.html" import render_field %}
    <form method=post action="/register">
      <dl>
        {{ render_field(form.username) }}
        {{ render_field(form.email) }}
        {{ render_field(form.password) }}
        {{ render_field(form.confirm) }}
        {{ render_field(form.accept_tos) }}
      </dl>
      <p><input type=submit value=Register>
    </form>

WTForms에 대한 더 많은 정보는, `WTForms website`_ 로 가서 살펴봐라.

.. _WTForms: http://wtforms.simplecodes.com/
.. _WTForms website: http://wtforms.simplecodes.com/
