Unicode in Flask
================

Flask like Jinja2 and Werkzeug is totally unicode based when it comes to
text.  Not only these libraries, also the majority of web related Python
libraries that deal with text.  If you don't know unicode so far, you
should probably read `The Absolute Minimum Every Software Developer
Absolutely, Positively Must Know About Unicode and Character Sets
<http://www.joelonsoftware.com/articles/Unicode.html>`_.  This part of the
documentation just tries to cover the very basics so that you have a
pleasent experience with unicode related things.

Automatic Conversion
--------------------

Flask has a few assumptions about your application (which you can change
of course) that give you basic and painless unicode support:

-   the encoding for text on your website is UTF-8
-   internally you will always use unicode exclusively for text except
    for literal strings with only ASCII character points.
-   encoding and decoding happens whenever you are talking over a protocol
    that requires bytes to be transmitted.

So what does this mean to you?

HTTP is based on bytes.  Not only the protocol, also the system used to
address documents on servers (so called URIs or URLs).  However HTML which
is usually transmitted on top of HTTP supports a large variety of
character sets and which ones are used, are transmitted in an HTTP header.
To not make this too complex Flask just assumes that if you are sending
unicode out you want it to be UTF-8 encoded.  Flask will do the encoding
and setting of the appropriate headers for you.

The same is true if you are talking to databases with the help of
SQLAlchemy or a similar ORM system.  Some databases have a protocol that
already transmits unicode and if they do not, SQLAlchemy or your other ORM
should take care of that.

The Golden Rule
---------------

So the rule of thumb: if you are not dealing with binary data, work with
unicode.  What does working with unicode in Python 2.x mean?

-   as long as you are using ASCII charpoints only (basically numbers,
    some special characters of latin letters without umlauts or anything
    fancy) you can use regular string literals (``'Hello World'``).
-   if you need anything else than ASCII in a string you have to mark
    this string as unicode string by prefixing it with a lowercase `u`.
    (like ``u'Hänsel und Gretel'``)
-   if you are using non-unicode characters in your Python files you have
    to tell Python which encoding your file uses.  Again, I recommend
    UTF-8 for this purpose.  To tell the interpreter your encoding you can
    put the ``# -*- coding: utf-8 -*-`` into the first or second line of
    your Python source file.

Encoding and Decoding Yourself
------------------------------

If you are talking with a filesystem or something that is not really based
on unicode you will have to ensure that you decode properly when working
with unicode interface.  So for example if you want to load a file on the
filesystem and embedd it into a Jinja2 template you will have to decode it
form the encoding of that file.  Here the old problem that textfiles do
not specify their encoding comes into play.  So do yourself a favour and
limit yourself to UTF-8 for textfiles as well.

Anyways.  To load such a file with unicode you can use the builtin
:meth:`str.decode` method::

    def read_file(filename, charset='utf-8'):
        with open(filename, 'r') as f:
            return f.read().decode(charset)

To go from unicode into a specific charset such as UTF-8 you can use the
:meth:`unicode.encode` method::

    def write_file(filename, contents, charset='utf-8'):
        with open(filename, 'w') as f:
            f.write(contents.encode(charset))
