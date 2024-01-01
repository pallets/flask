**Flask**
=====

**Flask** is a *lightweight* `WSGI`_ *web application framework*. It is designed
to make getting started **quick and easy**, with the ability to scale up to
complex applications. It began as a simple **wrapper** around `Werkzeug`_
and `Jinja`_ and has become one of the most popular **Python Web
Application Frameworks**.

**Flask** offers suggestions, but doesn't enforce any *dependencies or
project layout*. It is up to the **developer** to choose the *tools and
libraries* they want to use. There are many ``extensions`` provided by the
community that make adding new functionality easy.

.. _WSGI: https://wsgi.readthedocs.io/
.. _Werkzeug: https://werkzeug.palletsprojects.com/
.. _Jinja: https://jinja.palletsprojects.com/


**Installing**
----------

**Install & Update** using `pip`_:

.. code-block:: text

    $ pip install -U Flask

.. _pip: https://pip.pypa.io/en/stable/getting-started/


**A Simple Example**
----------------

.. code-block:: python

    # Save this as app.py
    from flask import Flask

    app = Flask(__name__)

    @app.route("/")
    def hello():
        return "Hello, World!"

.. code-block:: text

    $ flask run
      * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)


**Contributing**
------------

For guidance on setting up a *development environment* and how to make a
*contribution* to ``Flask``, see the `contributing guidelines`_.

.. _contributing guidelines: https://github.com/pallets/flask/blob/main/CONTRIBUTING.rst


**Donate**
------

The **Pallets** organization develops and supports ``Flask`` and the *libraries*
it uses. In order to grow the community of contributors and users, and
allow the maintainers to devote more time to the projects, `please
donate today`_.

.. _please donate today: https://palletsprojects.com/donate


**Links**
-----

-   **Documentation**: https://flask.palletsprojects.com/
-   **Changes**: https://flask.palletsprojects.com/changes/
-   **PyPI Releases**: https://pypi.org/project/Flask/
-   **Source Code**: https://github.com/pallets/flask/
-   **Issue Tracker**: https://github.com/pallets/flask/issues/
-   **Chat**: https://discord.gg/pallets

~~~~~

.. raw:: html

    <table>
        <tr>
            <td>
                <img src="https://img.shields.io/pypi/dm/Flask?style=for-the-badge" alt="Downloads in PyPi last month" width="200">
            </td>
            <td>
                <img src="https://img.shields.io/pypi/v/Flask?style=for-the-badge&logoColor=blue" alt="PyPi Package Version" width="116">
            </td>
        </tr>
    </table>

