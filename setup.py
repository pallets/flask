"""
Flask
-----

Flask is a microframework for Python based on Werkzeug, Jinja 2 and good
intentions. And before you ask: It's BSD licensed!

Flask is Fun
````````````

::

    from flask import Flask
    app = Flask(__name__)

    @app.route("/")
    def hello():
        return "Hello World!"

    if __name__ == "__main__":
        app.run()

And Easy to Setup
`````````````````

::

    $ easy_install Flask
    $ python hello.py
     * Running on http://localhost:5000/

Links
`````

* `website <http://flask.pocoo.org/>`_
* `documentation <http://flask.pocoo.org/docs/>`_
* `development version <http://github.com/mitsuhiko/flask/zipball/master#egg=Flask-dev>`_

"""
from setuptools import setup


setup(
    name='Flask',
    version='0.1',
    url='http://github.com/mitsuhiko/flask/',
    license='BSD',
    author='Armin Ronacher',
    author_email='armin.ronacher@active-4.com',
    description='A microframework based on Werkzeug, Jinja2 and good intentions',
    long_description=__doc__,
    py_modules=['flask'],
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Werkzeug>=0.6.1',
        'Jinja2>=2.4'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
