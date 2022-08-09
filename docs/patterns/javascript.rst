JavaScript, ``fetch``, and JSON
===============================

You may want to make your HTML page dynamic, by changing data without
reloading the entire page. Instead of submitting an HTML ``<form>`` and
performing a redirect to re-render the template, you can add
`JavaScript`_ that calls |fetch|_ and replaces content on the page.

|fetch|_ is the modern, built-in JavaScript solution to making
requests from a page. You may have heard of other "AJAX" methods and
libraries, such as |XHR|_ or `jQuery`_. These are no longer needed in
modern browsers, although you may choose to use them or another library
depending on your application's requirements. These docs will only focus
on built-in JavaScript features.

.. _JavaScript: https://developer.mozilla.org/Web/JavaScript
.. |fetch| replace:: ``fetch()``
.. _fetch: https://developer.mozilla.org/Web/API/Fetch_API
.. |XHR| replace:: ``XMLHttpRequest()``
.. _XHR: https://developer.mozilla.org/Web/API/XMLHttpRequest
.. _jQuery: https://jquery.com/


Rendering Templates
-------------------

It is important to understand the difference between templates and
JavaScript. Templates are rendered on the server, before the response is
sent to the user's browser. JavaScript runs in the user's browser, after
the template is rendered and sent. Therefore, it is impossible to use
JavaScript to affect how the Jinja template is rendered, but it is
possible to render data into the JavaScript that will run.

To provide data to JavaScript when rendering the template, use the
:func:`~jinja-filters.tojson` filter in a ``<script>`` block. This will
convert the data to a valid JavaScript object, and ensure that any
unsafe HTML characters are rendered safely. If you do not use the
``tojson`` filter, you will get a ``SyntaxError`` in the browser
console.

.. code-block:: python

    data = generate_report()
    return render_template("report.html", chart_data=data)

.. code-block:: jinja

    <script>
        const chart_data = {{ chart_data|tojson }}
        chartLib.makeChart(chart_data)
    </script>

A less common pattern is to add the data to a ``data-`` attribute on an
HTML tag. In this case, you must use single quotes around the value, not
double quotes, otherwise you will produce invalid or unsafe HTML.

.. code-block:: jinja

    <div data-chart='{{ chart_data|tojson }}'></div>


Generating URLs
---------------

The other way to get data from the server to JavaScript is to make a
request for it. First, you need to know the URL to request.

The simplest way to generate URLs is to continue to use
:func:`~flask.url_for` when rendering the template. For example:

.. code-block:: javascript

    const user_url = {{ url_for("user", id=current_user.id)|tojson }}
    fetch(user_url).then(...)

However, you might need to generate a URL based on information you only
know in JavaScript. As discussed above, JavaScript runs in the user's
browser, not as part of the template rendering, so you can't use
``url_for`` at that point.

In this case, you need to know the "root URL" under which your
application is served. In simple setups, this is ``/``, but it might
also be something else, like ``https://example.com/myapp/``.

A simple way to tell your JavaScript code about this root is to set it
as a global variable when rendering the template. Then you can use it
when generating URLs from JavaScript.

.. code-block:: javascript

    const SCRIPT_ROOT = {{ request.script_root|tojson }}
    let user_id = ...  // do something to get a user id from the page
    let user_url = `${SCRIPT_ROOT}/user/${user_id}`
    fetch(user_url).then(...)


Making a Request with ``fetch``
-------------------------------

|fetch|_ takes two arguments, a URL and an object with other options,
and returns a |Promise|_. We won't cover all the available options, and
will only use ``then()`` on the promise, not other callbacks or
``await`` syntax. Read the linked MDN docs for more information about
those features.

By default, the GET method is used. If the response contains JSON, it
can be used with a ``then()`` callback chain.

.. code-block:: javascript

    const room_url = {{ url_for("room_detail", id=room.id)|tojson }}
    fetch(room_url)
        .then(response => response.json())
        .then(data => {
            // data is a parsed JSON object
        })

To send data, use a data method such as POST, and pass the ``body``
option. The most common types for data are form data or JSON data.

To send form data, pass a populated |FormData|_ object. This uses the
same format as an HTML form, and would be accessed with ``request.form``
in a Flask view.

.. code-block:: javascript

    let data = new FormData()
    data.append("name": "Flask Room")
    data.append("description": "Talk about Flask here.")
    fetch(room_url, {
        "method": "POST",
        "body": data,
    }).then(...)

In general, prefer sending request data as form data, as would be used
when submitting an HTML form. JSON can represent more complex data, but
unless you need that it's better to stick with the simpler format. When
sending JSON data, the ``Content-Type: application/json`` header must be
sent as well, otherwise Flask will return a 400 error.

.. code-block:: javascript

    let data = {
        "name": "Flask Room",
        "description": "Talk about Flask here.",
    }
    fetch(room_url, {
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": JSON.stringify(data),
    }).then(...)

.. |Promise| replace:: ``Promise``
.. _Promise: https://developer.mozilla.org/Web/JavaScript/Reference/Global_Objects/Promise
.. |FormData| replace:: ``FormData``
.. _FormData: https://developer.mozilla.org/en-US/docs/Web/API/FormData


Following Redirects
-------------------

A response might be a redirect, for example if you logged in with
JavaScript instead of a traditional HTML form, and your view returned
a redirect instead of JSON. JavaScript requests do follow redirects, but
they don't change the page. If you want to make the page change you can
inspect the response and apply the redirect manually.

.. code-block:: javascript

    fetch("/login", {"body": ...}).then(
        response => {
            if (response.redirected) {
                window.location = response.url
            } else {
                showLoginError()
            }
        }
    )


Replacing Content
-----------------

A response might be new HTML, either a new section of the page to add or
replace, or an entirely new page. In general, if you're returning the
entire page, it would be better to handle that with a redirect as shown
in the previous section. The following example shows how to replace a
``<div>`` with the HTML returned by a request.

.. code-block:: html

    <div id="geology-fact">
        {{ include "geology_fact.html" }}
    </div>
    <script>
        const geology_url = {{ url_for("geology_fact")|tojson }}
        const geology_div = getElementById("geology-fact")
        fetch(geology_url)
            .then(response => response.text)
            .then(text => geology_div.innerHtml = text)
    </script>


Return JSON from Views
----------------------

To return a JSON object from your API view, you can directly return a
dict from the view. It will be serialized to JSON automatically.

.. code-block:: python

    @app.route("/user/<int:id>")
    def user_detail(id):
        user = User.query.get_or_404(id)
        return {
            "username": User.username,
            "email": User.email,
            "picture": url_for("static", filename=f"users/{id}/profile.png"),
        }

If you want to return another JSON type, use the
:func:`~flask.json.jsonify` function, which creates a response object
with the given data serialized to JSON.

.. code-block:: python

    from flask import jsonify

    @app.route("/users")
    def user_list():
        users = User.query.order_by(User.name).all()
        return jsonify([u.to_json() for u in users])

It is usually not a good idea to return file data in a JSON response.
JSON cannot represent binary data directly, so it must be base64
encoded, which can be slow, takes more bandwidth to send, and is not as
easy to cache. Instead, serve files using one view, and generate a URL
to the desired file to include in the JSON. Then the client can make a
separate request to get the linked resource after getting the JSON.


Receiving JSON in Views
-----------------------

Use the :attr:`~flask.Request.json` property of the
:data:`~flask.request` object to decode the request's body as JSON. If
the body is not valid JSON, or the ``Content-Type`` header is not set to
``application/json``, a 400 Bad Request error will be raised.

.. code-block:: python

    from flask import request

    @app.post("/user/<int:id>")
    def user_update(id):
        user = User.query.get_or_404(id)
        user.update_from_json(request.json)
        db.session.commit()
        return user.to_json()
