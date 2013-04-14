WTForms를 가지고 폼 유효성 확인하기
===================================

여러분이 브라우저에서 전송되는 폼 데이타를 가지고 작업해야할 때
곧 뷰 코드는 읽기가 매우 어려워진다.  이 과정을 더 쉽게 관리할 수 있도록
설계된 라이브러리들이 있다.  그것들 중 하나가 우리가 여기서 다룰 예정인
`WTForms`_  이다.  여러분이 많은 폼을 갖는 상황에 있다면, 이것을 한번
시도해보길 원할지도 모른다.

When you are working with WTForms you have to define your forms as classes
first.  I recommend breaking up the application into multiple modules 
(:ref:`larger-applications`) for that and adding a separate module for the
forms.

.. admonition:: Getting most of WTForms with an Extension

   The `Flask-WTF`_ extension expands on this pattern and adds a few
   handful little helpers that make working with forms and Flask more
   fun.  You can get it from `PyPI
   <http://pypi.python.org/pypi/Flask-WTF>`_.

.. _Flask-WTF: http://packages.python.org/Flask-WTF/

The Forms
---------

This is an example form for a typical registration page::

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

In the View
-----------

In the view function, the usage of this form looks like this::

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

Notice that we are implying that the view is using SQLAlchemy here
(:ref:`sqlalchemy-pattern`) but this is no requirement of course.  Adapt
the code as necessary.

Things to remember:

1. create the form from the request :attr:`~flask.request.form` value if
   the data is submitted via the HTTP `POST` method and
   :attr:`~flask.request.args` if the data is submitted as `GET`.
2. to validate the data, call the :func:`~wtforms.form.Form.validate`
   method which will return `True` if the data validates, `False`
   otherwise.
3. to access individual values from the form, access `form.<NAME>.data`.

Forms in Templates
------------------

Now to the template side.  When you pass the form to the templates you can
easily render them there.  Look at the following example template to see
how easy this is.  WTForms does half the form generation for us already.
To make it even nicer, we can write a macro that renders a field with
label and a list of errors if there are any.

Here's an example `_formhelpers.html` template with such a macro:

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

This macro accepts a couple of keyword arguments that are forwarded to
WTForm's field function that renders the field for us.  The keyword
arguments will be inserted as HTML attributes.  So for example you can
call ``render_field(form.username, class='username')`` to add a class to
the input element.  Note that WTForms returns standard Python unicode
strings, so we have to tell Jinja2 that this data is already HTML escaped
with the `|safe` filter.

Here the `register.html` template for the function we used above which
takes advantage of the `_formhelpers.html` template:

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

For more information about WTForms, head over to the `WTForms
website`_.

.. _WTForms: http://wtforms.simplecodes.com/
.. _WTForms website: http://wtforms.simplecodes.com/
