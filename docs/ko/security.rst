Security Considerations
=======================

Web applications usually face all kinds of security problems and it's very
hard to get everything right.  Flask tries to solve a few of these things
for you, but there are a couple more you have to take care of yourself.

.. _xss:

Cross-Site Scripting (XSS)
--------------------------

Cross site scripting is the concept of injecting arbitrary HTML (and with
it JavaScript) into the context of a website.  To remedy this, developers
have to properly escape text so that it cannot include arbitrary HTML
tags.  For more information on that have a look at the Wikipedia article
on `Cross-Site Scripting
<http://en.wikipedia.org/wiki/Cross-site_scripting>`_.

Flask configures Jinja2 to automatically escape all values unless
explicitly told otherwise.  This should rule out all XSS problems caused
in templates, but there are still other places where you have to be
careful:

-   generating HTML without the help of Jinja2
-   calling :class:`~flask.Markup` on data submitted by users
-   sending out HTML from uploaded files, never do that, use the
    `Content-Disposition: attachment` header to prevent that problem.
-   sending out textfiles from uploaded files.  Some browsers are using
    content-type guessing based on the first few bytes so users could
    trick a browser to execute HTML.

Another thing that is very important are unquoted attributes.  While
Jinja2 can protect you from XSS issues by escaping HTML, there is one
thing it cannot protect you from: XSS by attribute injection.  To counter
this possible attack vector, be sure to always quote your attributes with
either double or single quotes when using Jinja expressions in them:

.. sourcecode:: html+jinja

   <a href="{{ href }}">the text</a>

Why is this necessary?  Because if you would not be doing that, an
attacker could easily inject custom JavaScript handlers.  For example an
attacker could inject this piece of HTML+JavaScript:

.. sourcecode:: html

   onmouseover=alert(document.cookie)

When the user would then move with the mouse over the link, the cookie
would be presented to the user in an alert window.  But instead of showing
the cookie to the user, a good attacker might also execute any other
JavaScript code.  In combination with CSS injections the attacker might
even make the element fill out the entire page so that the user would
just have to have the mouse anywhere on the page to trigger the attack.

Cross-Site Request Forgery (CSRF)
---------------------------------

Another big problem is CSRF.  This is a very complex topic and I won't
outline it here in detail just mention what it is and how to theoretically
prevent it.

If your authentication information is stored in cookies, you have implicit
state management.  The state of "being logged in" is controlled by a
cookie, and that cookie is sent with each request to a page.
Unfortunately that includes requests triggered by 3rd party sites.  If you
don't keep that in mind, some people might be able to trick your
application's users with social engineering to do stupid things without
them knowing.

Say you have a specific URL that, when you sent `POST` requests to will
delete a user's profile (say `http://example.com/user/delete`).  If an
attacker now creates a page that sends a post request to that page with
some JavaScript they just has to trick some users to load that page and
their profiles will end up being deleted.

Imagine you were to run Facebook with millions of concurrent users and
someone would send out links to images of little kittens.  When users
would go to that page, their profiles would get deleted while they are
looking at images of fluffy cats.

How can you prevent that?  Basically for each request that modifies
content on the server you would have to either use a one-time token and
store that in the cookie **and** also transmit it with the form data.
After receiving the data on the server again, you would then have to
compare the two tokens and ensure they are equal.

Why does Flask not do that for you?  The ideal place for this to happen is
the form validation framework, which does not exist in Flask.

.. _json-security:

JSON Security
-------------

.. admonition:: ECMAScript 5 Changes

   Starting with ECMAScript 5 the behavior of literals changed.  Now they
   are not constructed with the constructor of ``Array`` and others, but
   with the builtin constructor of ``Array`` which closes this particular
   attack vector.

JSON itself is a high-level serialization format, so there is barely
anything that could cause security problems, right?  You can't declare
recursive structures that could cause problems and the only thing that
could possibly break are very large responses that can cause some kind of
denial of service at the receiver's side.

However there is a catch.  Due to how browsers work the CSRF issue comes
up with JSON unfortunately.  Fortunately there is also a weird part of the
JavaScript specification that can be used to solve that problem easily and
Flask is kinda doing that for you by preventing you from doing dangerous
stuff.  Unfortunately that protection is only there for
:func:`~flask.jsonify` so you are still at risk when using other ways to
generate JSON.

So what is the issue and how to avoid it?  The problem are arrays at
top-level in JSON.  Imagine you send the following data out in a JSON
request.  Say that's exporting the names and email addresses of all your
friends for a part of the user interface that is written in JavaScript.
Not very uncommon:

.. sourcecode:: javascript

    [
        {"username": "admin",
         "email": "admin@localhost"}
    ]

And it is doing that of course only as long as you are logged in and only
for you.  And it is doing that for all `GET` requests to a certain URL,
say the URL for that request is
``http://example.com/api/get_friends.json``.

So now what happens if a clever hacker is embedding this to his website
and social engineers a victim to visiting his site:

.. sourcecode:: html

    <script type=text/javascript>
    var captured = [];
    var oldArray = Array;
    function Array() {
      var obj = this, id = 0, capture = function(value) {
        obj.__defineSetter__(id++, capture);
        if (value)
          captured.push(value);
      };
      capture();
    }
    </script>
    <script type=text/javascript
      src=http://example.com/api/get_friends.json></script>
    <script type=text/javascript>
    Array = oldArray;
    // now we have all the data in the captured array.
    </script>

If you know a bit of JavaScript internals you might know that it's
possible to patch constructors and register callbacks for setters.  An
attacker can use this (like above) to get all the data you exported in
your JSON file.  The browser will totally ignore the ``application/json``
mimetype if ``text/javascript`` is defined as content type in the script
tag and evaluate that as JavaScript.  Because top-level array elements are
allowed (albeit useless) and we hooked in our own constructor, after that
page loaded the data from the JSON response is in the `captured` array.

Because it is a syntax error in JavaScript to have an object literal
(``{...}``) toplevel an attacker could not just do a request to an
external URL with the script tag to load up the data.  So what Flask does
is to only allow objects as toplevel elements when using
:func:`~flask.jsonify`.  Make sure to do the same when using an ordinary
JSON generate function.
