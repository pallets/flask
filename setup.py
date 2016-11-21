"""
Flask
-----

Flask is a microframework for Python based on Werkzeug, Jinja 2 and good
intentions. And before you ask: It's BSD licensed!

Flask is Fun
````````````

Save in a hello.py:

.. code:: python

    from flask import Flask
    app = Flask(__name__)

    @app.route("/")
    def hello():
        return "Hello World!"

    if __name__ == "__main__":
        app.run()

And Easy to Setup
`````````````````

And run it:

.. code:: bash

    $ pip install Flask
    $ python hello.py
     * Running on http://localhost:5000/

 Ready for production? `Read this first <http://flask.pocoo.org/docs/deploying/>`.

Links
`````

* `website <http://flask.pocoo.org/>`_
* `documentation <http://flask.pocoo.org/docs/>`_
* `development version
  <http://github.com/pallets/flask/zipball/master#egg=Flask-dev>`_

"""
import re
import ast
from setuptools import setup


_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('flask/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))


setup(
    name='Flask',
    version=version,
    url='http://github.com/pallets/flask/',
    license='BSD',
    author='Armin Ronacher',
    author_email='armin.ronacher@active-4.com',
    description='A microframework based on Werkzeug, Jinja2 '
                'and good intentions',
    long_description=__doc__,
    packages=['flask', 'flask.ext'],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Werkzeug>=0.7',
        'Jinja2>=2.4',
        'itsdangerous>=0.21',
        'click>=2.0',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    entry_points='''
        [console_scripts]
        flask=flask.cli:main
    '''
)
