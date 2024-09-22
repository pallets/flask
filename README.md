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

## Installation Instructions
To install Flask, pip, the package manager included with Python, is used.
It is considered best practice to start a Flask project within a virtual
environment. This practice ensures that any packages installed are confined
to the virtual environment, keeping them separate from the global environment
of the system. By doing so, it prevents potential conflicts between package
versions, maintaining compatibility and stability across different projects.



To create a virtual environment run the command:
```
python -m venv venv
```

To activate a virtual environment on Windows:
```
.\venv\Scripts\activate
```

To activate a virtual environment on macOS and Linux:
```
source venv/bin/activate
```

To install the flask python package run the command:
```
pip install flask
```

To deactivate the virtual environment run the command:
```
deactivate
```

## Donate

The Pallets organization develops and supports Flask and the libraries
it uses. In order to grow the community of contributors and users, and
allow the maintainers to devote more time to the projects, [please
donate today][].

[please donate today]: https://palletsprojects.com/donate
