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
<https://en.wikipedia.org/wiki/Cross-site_scripting>`_.

Flask configures Jinja2 to automatically escape all values unless
explicitly told otherwise.  This should rule out all XSS problems caused
in templates, but there are still other places where you have to be
careful:

-   generating HTML without the help of Jinja2
-   calling :class:`~flask.Markup` on data submitted by users
-   sending out HTML from uploaded files, never do that, use the
    ``Content-Disposition: attachment`` header to prevent that problem.
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

Say you have a specific URL that, when you sent ``POST`` requests to will
delete a user's profile (say ``http://example.com/user/delete``).  If an
attacker now creates a page that sends a post request to that page with
some JavaScript they just have to trick some users to load that page and
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

In Flask 0.10 and lower, :func:`~flask.jsonify` did not serialize top-level
arrays to JSON. This was because of a security vulnerability in ECMAScript 4.

ECMAScript 5 closed this vulnerability, so only extremely old browsers are
still vulnerable. All of these browsers have `other more serious
vulnerabilities
<https://github.com/pallets/flask/issues/248#issuecomment-59934857>`_, so
this behavior was changed and :func:`~flask.jsonify` now supports serializing
arrays.

Security Headers
----------------

This section contains a list of HTTP security headers supported by Flask.
To configure HTTPS and handle the headers listed below we suggest the package `flask-talisman <https://github.com/GoogleCloudPlatform/flask-talisman>`_. 

HTTP Strict Transport Security (HSTS)
-------------------------------------

Redirects HTTP requests to HTTPS on all URLs, preventing man-in-the-middle (MITM) attacks.

Example:

.. sourcecode:: none
   
   Strict-Transport-Security: max-age=<expire-time 
   Strict-Transport-Security: max-age=<expire-time>; includeSubDomains 
   Strict-Transport-Security: max-age=<expire-time>; preload 

See also `Strict Transport Security <https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security>`_. 

HTTP Public Key Pinning (HPKP)
------------------------------

This enables your web server to authenticate with a client browser using a specific certificate key to prevent man-in-the-middle (MITM) attacks.

Example:

.. sourcecode:: none

   Public-Key-Pins: pin-sha256="base64=="; max-age=expireTime [; includeSubDomains][; report-uri="reportURI"] 

See also `Public Key Pinning <https://developer.mozilla.org/en-US/docs/Web/HTTP/Public_Key_Pinning>`_.

X-Frame-Options (Clickjacking Protection)
-----------------------------------------

Prevents the client from clicking page elements outside of the website, avoiding hijacking or UI redress attacks.

.. sourcecode:: none
   
   X-Frame-Options: DENY 
   X-Frame-Options: SAMEORIGIN
   X-Frame-Options: ALLOW-FROM https://example.com/

See also `X-Frame-Options <https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options>`_. 

X-Content-Type-Options
----------------------

This header prevents Cross-site scripting (XSS) by blocking requests on clients and forcing them to first read and validate the content-type before reading any of the contents of the request.

.. sourcecode:: none
   
   X-Content-Type-Options: nosniff

See also `X-Content-Type-Options <https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Content-Type-Options>`_. 

Content Security Policy (CSP)
-----------------------------

Enhances security and prevents common web vulnerabilities such as cross-site scripting (XSS) and man-in-the-middle (MITM) related attacks.

Example:

.. sourcecode:: none
   
   Content-Security-Policy: default-src https:; script-src 'nonce-{random}'; object-src 'none'

See also `Content Security Policy <https://csp.withgoogle.com/docs/index.html>`_.

Cookie Options
--------------

While these headers are not directly security related, they have important options that may affect your Flask application.

- ``Secure`` limits your cookies to HTTPS traffic only.
- ``HttpOnly`` protects the contents of your cookie from being visible to XSS.
- ``SameSite`` ensures that cookies can only be requested from the same domain that created them but this feature is not yet fully supported across all browsers.  

Example:

.. sourcecode:: none
   
   Set-Cookie: [cookie-name]=[cookie-value] 

See also:

-  Mozilla guide to `HTTP cookies <https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies#Secure_and_HttpOnly_cookies>`_.
- `OWASP HTTP Only <https://www.owasp.org/index.php/HttpOnly>`_. 
