# Flask

Flask is a lightweight [WSGI] web application framework. It is designed
to make getting started quick and easy, with the ability to scale up to
complex applications. It began as a simple wrapper around [Werkzeug]
and [Jinja], and has grown into one of the most popular Python web
frameworks in the world.

Flask provides a minimal core with no enforced project layout, allowing
developers to choose the tools and libraries they prefer. Its flexibility
makes it an excellent choice for both small projects and enterprise-grade
applications.

[WSGI]: https://wsgi.readthedocs.io/
[Werkzeug]: https://werkzeug.palletsprojects.com/
[Jinja]: https://jinja.palletsprojects.com/

## Why Flask?

- Minimal by design – no rigid structure, full freedom of choice.
- Scalable from small scripts to large applications.
- Extensible through a rich ecosystem of extensions.
- Backed by strong documentation and a large, active community.

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

## Donate

The Pallets organization maintains Flask and its ecosystem.
To help grow the community and support long-term development,
[please consider donating today].

[please consider donating today]: https://palletsprojects.com/donate

## Contributing

Flask welcomes all types of contributions, including:
- Reporting bugs or proposing improvements
- Discussing or suggesting features
- Improving the documentation
- Reviewing or submitting pull requests

To get started, see our [contributing guide][contrib].

[contrib]: https://palletsprojects.com/contributing/
