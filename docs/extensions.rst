.. _extensions:

Extensions
==========

Extensions are extra packages that add functionality to a Flask
application. For example, an extension might add support for sending
email or connecting to a database. Some extensions add entire new
frameworks to help build certain types of applications, like a ReST API.


Finding Extensions
------------------

Flask extensions are usually named "Flask-Foo" or "Foo-Flask". Many
extensions are listed in the `Extension Registry`_, which can be updated
by extension developers. You can also search PyPI for packages tagged
with `Framework :: Flask <pypi_>`_.


Using Extensions
----------------

Consult each extension's documentation for installation, configuration,
and usage instructions. Generally, extensions pull their own
configuration from :attr:`app.config <flask.Flask.config>` and are
passed an application instance during initialization. For example,
an extension caled "Flask-Foo" might be used like this::

    from flask_foo import Foo

    foo = Foo()

    app = Flask(__name__)
    app.config.update(
        FOO_BAR='baz',
        FOO_SPAM='eggs',
    )

    foo.init_app(app)


Building Extensions
-------------------

While the `Extension Registry`_ contains many Flask extensions, you may
not find an extension that fits your need. If this is the case, you can
create your own. Read :ref:`extension-dev` to develop your own Flask
extension.


.. _Extension Registry: http://flask.pocoo.org/extensions/
.. _pypi: https://pypi.org/search/?c=Framework+%3A%3A+Flask
