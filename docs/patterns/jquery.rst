AJAX With jQuery
================

`jQuery`_ is a small JavaScript library commonly used to simplify working
with the DOM and JavaScript in general.  It is the perfect tool to make
web applications more dynamic by exchanging JSON between server and
client.

.. _jQuery: http://jquery.com/

Loading jQuery
--------------

In order to use jQuery, you have to download it first and place it in the
static folder of your application and then ensure it's loaded.  Ideally
you have a layout template that is used for all pages where you just have
to add two script statements to your `head` section.  One for jQuery, and
one for your own script (called `app.js` here):

.. sourcecode:: html

   <script type=text/javascript src="{{
       url_for('static', filename='jquery.js') }}"></script>
   <script type=text/javascript src="{{
       url_for('static', filename='app.js') }}"></script>

Where is My Site?
-----------------

Do you know where your application is?  If you are developing the answer
is quite simple: it's on localhost port something and directly on the root
of that server.  But what if you later decide to move your application to
a different location?  For example to ``http://example.com/myapp``?  On
the server side this never was a problem because we were using the handy
:func:`~flask.url_for` function that did could answer that question for
us, but if we are using jQuery we should better not hardcode the path to
the application but make that dynamic, so how can we do that?

A simple method would be to add a script tag to our page that sets a
global variable to the prefix to the root of the application.  Something
like this:

.. sourcecode:: html+jinja

   <script type=text/javascript>
     $SCRIPT_ROOT = {{ request.script_root|tojson|safe }};
   </script>

The ``|safe`` is necessary so that Jinja does not escape the JSON encoded
string with HTML rules.  Usually this would be necessary, but we are
inside a `script` block here where different rules apply.

.. admonition:: Information for Pros

   In HTML the `script` tag is declared `CDATA` which means that entities
   will not be parsed.  Everything until ``</script>`` is handled as script.
   This also means that there must never be any ``</`` between the script
   tags.  ``|tojson`` is kindly enough to do the right thing here and
   escape backslashes for you.
