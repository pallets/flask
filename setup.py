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
* `development version
  <http://github.com/mitsuhiko/flask/zipball/master#egg=Flask-dev>`_

"""
from setuptools import Command, setup

class run_audit(Command):
    """Audits source code using PyFlakes for following issues:
        - Names which are used but not defined or used before they are defined.
        - Names which are redefined without having been used.
    """
    description = "Audit source code with PyFlakes"
    user_options = []

    def initialize_options(self):
        all = None

    def finalize_options(self):
        pass

    def run(self):
        import os, sys
        try:
            import pyflakes.scripts.pyflakes as flakes
        except ImportError:
            print "Audit requires PyFlakes installed in your system."""
            sys.exit(-1)

        dirs = ['flask', 'tests']
        # Add example directories
        for dir in ['flaskr', 'jqueryexample', 'minitwit']:
            dirs.append(os.path.join('examples', dir))
        # TODO: Add test subdirectories
        warns = 0
        for dir in dirs:
            for filename in os.listdir(dir):
                if filename.endswith('.py') and filename != '__init__.py':
                    warns += flakes.checkPath(os.path.join(dir, filename))
        if warns > 0:
            print ("Audit finished with total %d warnings." % warns)
        else:
            print ("No problems found in sourcecode.")

def run_tests():
    import os, sys
    sys.path.append(os.path.join(os.path.dirname(__file__), 'tests'))
    from flask_tests import suite
    return suite()


setup(
    name='Flask',
    version='0.7.1',
    url='http://github.com/mitsuhiko/flask/',
    license='BSD',
    author='Armin Ronacher',
    author_email='armin.ronacher@active-4.com',
    description='A microframework based on Werkzeug, Jinja2 '
                'and good intentions',
    long_description=__doc__,
    packages=['flask'],
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Werkzeug>=0.6.1',
        'Jinja2>=2.4'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    cmdclass={'audit': run_audit},
    test_suite='__main__.run_tests'
)
