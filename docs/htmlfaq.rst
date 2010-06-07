HTML/XHTML FAQ
==============

The Flask documentation and example applications are using HTML5.  You
will notice that in many situations when end tags are optional they are
not used to keep the HTML cleaner and also faster to load.  Because there
is a lot of confusion about HTML and XHTML out there this document tries
to answer some of them.


History on XHTML
----------------

For a while it looked like HTML was about to be replaced by XHTML.
However barely any websites on the internet are actually real XHTML (which
means XHTML processed with XML rules).  There are a couple of reasons why
this is the case.  It mostly has to do with Internet Explorer which does
not accept the XHTML mimetype to switch the browser into XML mode.
However this is really easy to bypass but barely anyone does that.  This
probably has to do with the fact that XHTML is really painful.

Why is it painful?  XML has very strict errorhandling.  On a parsing error
the browser is supposed to show the user an ugly error message.  Most of
the (X)HTML generation on the web is based on non-XML template engines
(such as Jinja, the one used in Flask) which do not protect you from
accidentally creating invalid HTML.  There are XML based template engines
but they usually come with a larger runtime overhead and are not as
straightforward to use because they have to obey XML rules.

Now the majority of users assumed they were using XHTML though.  The
reasons for that is that they sticked an XHTML doctype on top of the
document and self-closed all necessary tags (``<br>`` becomes ``<br/>`` or
``<br></br>`` in XHTML).  However even if the document properly validates
as XHTML there are still other things to keep in mind.

XHTML also changes the way you work with JavaScript because you now have
to use the namespaced DOM interface with the XHTML namespace to query for
HTML elements.

History of HTML5
----------------

HTML5 was started in 2004 under the name Web Applications 1.0 by the
WHATWG (Apple, Mozilla, Opera) and the idea was to write a new and
improved specification of HTML based on actual browser behaviour instead
of behaviour that exists on the paper but could not be implemented
because of backwards compatibility with the already existing web.

For example in theory HTML4 ``<title/Hello/`` means exactly the same as
``<title>Hello</title>`` but because existing websites are using
pseudo-XHTML which uses the Slash in different ways, this could not be
implemented properly.

In 2007 the specification was adopted as the basis of a new HTML
specification under the umbrella of the W3C.  Currently it looks like
XHTML is losing traction, the XHTML 2 working group was disbanded and
HTML5 is being implemented by all major browser vendors.

HTML versus XHTML
-----------------

The following table gives you a quick overview of features available in
HTML 4.01, XHTML 1.1 and HTML5 (we are not looking at XHTML 1.0 here which
was superceeded by XHTML 1.1 or XHTML5 which is barely supported currently):

+-----------------------------------------+----------+----------+----------+
|                                         | HTML4.01 | XHTML1.1 | HTML5    |
+=========================================+==========+==========+==========+
| ``<tag/value/`` == ``<tag>value</tag>`` | |Y| [1]_ | |N|      | |N|      |
+-----------------------------------------+----------+----------+----------+
| ``<br/>`` supported                     | |N|      | |Y|      | |Y| [2]_ |
+-----------------------------------------+----------+----------+----------+
| ``<script/>`` supported                 | |N|      | |Y|      | |N|      |
+-----------------------------------------+----------+----------+----------+
| might be served as `text/html`          | |Y|      | |N| [3]_ | |Y|      |
+-----------------------------------------+----------+----------+----------+
| might be served as                      | |N|      | |Y|      | |N|      |
| `application/xml+html`                  |          |          |          |
+-----------------------------------------+----------+----------+----------+
| strict error handling                   | |N|      | |Y|      | |N|      |
+-----------------------------------------+----------+----------+----------+
| inline SVG                              | |N|      | |Y|      | |Y|      |
+-----------------------------------------+----------+----------+----------+
| inline MathML                           | |N|      | |Y|      | |Y|      |
+-----------------------------------------+----------+----------+----------+
| ``<video>`` tag                         | |N|      | |N|      | |Y|      |
+-----------------------------------------+----------+----------+----------+
| ``<audio>`` tag                         | |N|      | |N|      | |Y|      |
+-----------------------------------------+----------+----------+----------+
| New semantical tags like ``<article>``  | |N|      | |N|      | |Y|      |
+-----------------------------------------+----------+----------+----------+

.. [1] Obscure feature inherited from SGML not supported by browsers
.. [2] For compatibility with XHTML generating server code for some
       tags such as ``<br>``.  Should not be used.
.. [3] XHTML 1.0 is the last XHTML standard that allows to be served
       as `text/html` for backwards compatibility reasons.

.. |Y| image:: _static/yes.png
       :alt: Yes
.. |N| image:: _static/no.png
       :alt: No

What does Strict Mean?
----------------------

HTML5 has strictly defined parsing rules, but it also specifies how a
browser should react to parsing errors.  Some things people stumble upon
with HTML5 and older HTML standards is that browsers will accept some
things that still create the expected output even though it looks wrong
(eg: certain tags are missing or are not closed).

Some of that is caused by the error handling browsers use if they
encounter a markup error, others are actually specified.  The following
things are optional in HTML5 by standard and have to be supported by
browsers (and are supported):

-   ``<html>``, ``<head>`` or ``<body>``
-   The closing tags for ``<p>``, ``<li>``, ``<dl>``, ``<dd>``, ``<tr>``,
    ``<td>``, ``<th>``, ``<tbody>``, ``<thead>``, ``<tfoot>``.
-   quotes for attribtues if they contain no whitespace and some
    special chars that require quoting.

This means the following piece of HTML5 is perfectly valid:

.. sourcecode:: html

    <!doctype html>
    <title>Hello HTML5</title>
    <div class=header>
      <h1>Hello HTML5</h1>
      <p class=tagline>HTML5 is awesome
    </div>
    <ul class=nav>
      <li><a href=/index>Index</a>
      <li><a href=/downloads>Downloads</a>
      <li><a href=/about>About</a>
    </ul>
    <div class=body>
      <h2>HTML5 is probably the future</h2>
      <p>
        There might be some other things around but in terms of
        browser vendor support, HTML5 is hard to beat.
      <dl>
        <dt>Key 1
        <dd>Value 1
        <dt>Key 2
        <dd>Value 2
      </dl>
    </div>


What should be used?
--------------------

Currently the answer is HTML5.  There are very few reasons to use XHTML
with the latest development.  There are some companies successfully using
actual XML and XSLT on the client side with fallbacks to server side HTML4
generation for browsers not supporting XML and XSLT but but it's not very
common.  Now that MathML and SVG landed in HTML5 and with the sad support
for XHTML in Internet Explorer and many JavaScript libraries for most
applications no reasons remain to use XHTML.
