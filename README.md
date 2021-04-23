![PyPi Version](https://img.shields.io/pypi/v/flask)
![License](https://img.shields.io/github/license/pallets/flask)
[![Tests](https://github.com/pallets/flask/actions/workflows/tests.yaml/badge.svg)](https://github.com/pallets/flask/actions/workflows/tests.yaml)


Flask
=====

Flask is a lightweight [WSGI]( https://wsgi.readthedocs.io/) web application framework. It is designed
to make getting started quick and easy, with the ability to scale up to
complex applications. It began as a simple wrapper around [Werkzeug](https://werkzeug.palletsprojects.com/)
and [Jinja](https://jinja.palletsprojects.com/) and has become one of the most popular Python web
application frameworks.

Flask offers suggestions, but doesn't enforce any dependencies or
project layout. It is up to the developer to choose the tools and
libraries they want to use. There are many extensions provided by the
community that make adding new functionality easy.


Installing
----------

Install and update using [pip](https://pip.pypa.io/en/stable/quickstart/):

`$ pip install -U Flask`

If you get an error, it is most likely that pip is not installed. Checks [this](https://pip.pypa.io/en/stable/installing/).

A Simple Example
----------------

```py
# save this as app.py
from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, World!"
```
```
$ flask run
    * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

Contributing
------------

For guidance on setting up a development environment and how to make a
contribution to Flask, see the [contributing guidelines](https://github.com/pallets/flask/blob/master/CONTRIBUTING.rst).



Donate
------

The Pallets organization develops and supports Flask and the libraries
it uses. In order to grow the community of contributors and users, and
allow the maintainers to devote more time to the projects, [please
donate today](https://palletsprojects.com/donate).


Links
-----

-   [Documentation](https://flask.palletsprojects.com/)
-   [Changes](https://flask.palletsprojects.com/changes/)
-   [PyPI Releases](https://pypi.org/project/Flask/)
-   [Source Code](https://github.com/pallets/flask/)
-   [Issue Tracker](https://github.com/pallets/flask/issues/)
-   [Website](https://palletsprojects.com/p/flask/)
-   [Twitter](https://twitter.com/PalletsTeam)
-   [Chat](https://discord.gg/pallets)
