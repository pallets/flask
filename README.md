# Flask

Flask is a lightweight [WSGI][] web application framework. It is designed
to make getting started quick and easy, with the ability to scale up to
complex applications. It began as a simple wrapper around [Werkzeug][]
and [Jinja][], and has become one of the most popular Python web
application frameworks.

Flask offers suggestions, but doesn't enforce any dependencies or
project layout. It is up to the developer to choose the tools and
libraries they want to use. There are many extensions provided by the
community that make adding new functionality easy.

[WSGI]: https://wsgi.readthedocs.io/
[Werkzeug]: https://werkzeug.palletsprojects.com/
[Jinja]: https://jinja.palletsprojects.com/


## Installing

Install and update from [PyPI][] using an installer such as [pip][]:

```
$ pip install -U Flask
```

[PyPI]: https://pypi.org/project/Flask/
[pip]: https://pip.pypa.io/en/stable/getting-started/


## A Simple Example

```python
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


## Contributing

For guidance on setting up a development environment and how to make a
contribution to Flask, see the [contributing guidelines][].

[contributing guidelines]: https://github.com/pallets/flask/blob/main/CONTRIBUTING.rst


## Donate

The Pallets organization develops and supports Flask and the libraries
it uses. In order to grow the community of contributors and users, and
allow the maintainers to devote more time to the projects, [please
donate today][].

[please donate today]: https://palletsprojects.com/donate
