.. _tutorial-templates:

Step 6: The Templates
=====================

Now we should start working on the templates.  If we request the URLs now
we would only get an exception that Flask cannot find the templates.  The
templates are using `Jinja2`_ syntax and have autoescaping enabled by
default.  This means that unless you mark a value in the code with
:class:`~flask.Markup` or with the ``|safe`` filter in the template,
Jinja2 will ensure that special characters such as ``<`` or ``>`` are
escaped with their XML equivalents.

We are also using template inheritance which makes it possible to reuse
the layout of the website in all pages.

Put the following templates into the `templates` folder:

.. _Jinja2: http://jinja.pocoo.org/2/documentation/templates

layout.html
-----------

This template contains the HTML skeleton, the header and a link to log in
(or log out if the user was already logged in).  It also displays the
flashed messages if there are any.  The ``{% block body %}`` block can be
replaced by a block of the same name (``body``) in a child template.

The :class:`~flask.session` dict is available in the template as well and
you can use that to check if the user is logged in or not.  Note that in
Jinja you can access missing attributes and items of objects / dicts which
makes the following code work, even if there is no ``'logged_in'`` key in
the session:

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

This template extends the `layout.html` template from above to display the
messages.  Note that the `for` loop iterates over the messages we passed
in with the :func:`~flask.render_template` function.  We also tell the
form to submit to your `add_entry` function and use `POST` as `HTTP`
method:

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

Finally the login template which basically just displays a form to allow
the user to login:

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

Continue with :ref:`tutorial-css`.
