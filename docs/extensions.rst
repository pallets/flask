.. _extensions:

Extensions
==========

Extensions are extra packages that add functionality to a Flask
application. For example, an extension might add support for sending
email or connecting to a database. Some extensions add entire new
frameworks to help build certain types of applications, like a REST API.


Finding Extensions
------------------

Flask extensions are usually named "Flask-Foo" or "Foo-Flask". You can
search PyPI for packages tagged with `Framework :: Flask <pypi_>`_.


Using Extensions
----------------

Consult each extension's documentation for installation, configuration,
and usage instructions. Generally, extensions pull their own
configuration from :attr:`app.config <flask.Flask.config>` and are
passed an application instance during initialization. For example,
an extension called "Flask-Foo" might be used like this::

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

While the `PyPI <pypi_>`_ contains many Flask extensions, you may
not find an extension that fits your need. If this is the case, you can
create your own. Read :doc:`/extensiondev` to develop your own Flask
extension.


.. _pypi: https://pypi.org/search/?c=Framework+%3A%3A+Flask
