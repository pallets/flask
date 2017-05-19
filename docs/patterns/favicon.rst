Adding a favicon
================

A "favicon" is an icon used by browsers for tabs and bookmarks. This helps
to distinguish your website and to give it a unique brand.

A common question is how to add a favicon to a Flask application. First, of
course, you need an icon. It should be 16 × 16 pixels and in the ICO file
format. This is not a requirement but a de-facto standard supported by all
relevant browsers. Put the icon in your static directory as
:file:`favicon.ico`.

Now, to get browsers to find your icon, the correct way is to add a link
tag in your HTML. So, for example:

.. sourcecode:: html+jinja

    <link rel="shortcut icon" href="{{ url_for('static', filename='favicon.ico') }}">

That's all you need for most browsers, however some really old ones do not
support this standard. The old de-facto standard is to serve this file,
with this name, at the website root. If your application is not mounted at
the root path of the domain you either need to configure the web server to
serve the icon at the root or if you can't do that you're out of luck. If
however your application is the root you can simply route a redirect::

    app.add_url_rule('/favicon.ico',
                     redirect_to=url_for('static', filename='favicon.ico'))

If you want to save the extra redirect request you can also write a view
using :func:`~flask.send_from_directory`::

    import os
    from flask import send_from_directory

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'),
                                   'favicon.ico', mimetype='image/vnd.microsoft.icon')

We can leave out the explicit mimetype and it will be guessed, but we may
as well specify it to avoid the extra guessing, as it will always be the
same.

The above will serve the icon via your application and if possible it's
better to configure your dedicated web server to serve it; refer to the
web server's documentation.

See also
--------

* The `Favicon <https://en.wikipedia.org/wiki/Favicon>`_ article on
  Wikipedia
