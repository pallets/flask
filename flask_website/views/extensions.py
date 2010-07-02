from urlparse import urlparse
from flask import Module, render_template, Markup
from werkzeug import url_quote

extensions = Module(__name__, url_prefix='/extensions')

class Extension(object):

    def __init__(self, name, author, description,
                 github=None, bitbucket=None, docs=None, website=None):
        self.name = name
        self.author = author
        self.description = Markup(description)
        self.github = github
        self.bitbucket = bitbucket
        self.docs = docs
        self.website = website

    @property
    def pypi(self):
        return 'http://pypi.python.org/pypi/%s' % url_quote(self.name)

    @property
    def docserver(self):
        if self.docs:
            return urlparse(self.docs)[1]

database = [
    Extension('Flask-OAuth', 'Armin Ronacher',
        description='''
            <p>Adds <a href="http://oauth.net/">OAuth</a> support to Flask.
        ''',
        github='mitsuhiko/flask-oauth',
        docs='http://packages.python.org/Flask-OAuth/'
    ),
    Extension('Flask-OpenID', 'Armin Ronacher',
        description='''
            <p>Adds <a href="http://openid.net/">OpenID</a> support to Flask.
        ''',
        github='mitsuhiko/flask-openid',
        docs='http://packages.python.org/Flask-OpenID/'
    ),
    Extension('Flask-Babel', 'Armin Ronacher',
        description='''
            <p>Adds i18n/l10n support to Flask, based on
            <a href=http://babel.edgewall.org/>babel</a> and
            <a href=http://pytz.sourceforge.net/>pytz</a>.
        ''',
        github='mitsuhiko/flask-babel',
        docs='http://packages.python.org/Flask-Babel/'
    ),
    Extension('Flask-SQLAlchemy', 'Armin Ronacher',
        description='''
            <p>Adds SQLAlchemy support to Flask.  Quick and easy.
        ''',
        github='mitsuhiko/flask-sqlalchemy',
        docs='http://packages.python.org/Flask-SQLAlchemy/'
    ),
    Extension('Flask-XML-RPC', 'Matthew Frazier',
        description='''
            <p>Adds <a href="http://www.xmlrpc.com/">XML-RPC</a> support to Flask.
        ''',
        bitbucket='leafstorm/flask-xml-rpc',
        docs='http://packages.python.org/Flask-XML-RPC/'
    ),
    Extension('Flask-CouchDB', 'Matthew Frazier',
        description='''
            <p>Adds <a href="http://couchdb.apache.org/">CouchDB</a> support to Flask.
        ''',
        bitbucket='leafstorm/flask-couchdb',
        docs='http://packages.python.org/Flask-CouchDB/'
    ),
    Extension('Flask-Genshi', 'Dag Odenhall',
        description='''
            <p>Adds support for the <a href="http://genshi.edgewall.org/">Genshi</a>
            templating language to Flask applications.
        ''',
        bitbucket='dag/flask-genshi',
        docs='http://packages.python.org/Flask-Genshi/'
    ),
    Extension('flask-mail', 'Dan Jacob',
        description='''
            <p>Makes sending mails from Flask applications very easy and
            has also support for unittesting.
        ''',
        bitbucket='danjac/flask-mail',
        docs='http://packages.python.org/flask-mail/'
    ),
    Extension('Flask-WTF', 'Dan Jacob',
        description='''
            <p>Flask-WTF offers simple integration with WTForms. This
            integration includes optional CSRF handling for greater security.
        ''',
        bitbucket='danjac/flask-wtf',
        docs='http://packages.python.org/Flask-WTF/'
    ),
    Extension('Flask-Testing', 'Dan Jacob',
        description='''
            <p>The Flask-Testing extension provides unit testing utilities for Flask.
        ''',
        bitbucket='danjac/flask-testing',
        docs='http://packages.python.org/Flask-Testing/'
    ),
    Extension('flask-csrf', 'Steve Losh',
        description='''
            <p>A small Flask extension for adding
            <a href=http://en.wikipedia.org/wiki/CSRF>CSRF</a> protection.
        ''',
        docs='http://sjl.bitbucket.org/flask-csrf/',
        bitbucket='sjl/flask-csrf'
    ),
    Extension('flask-lesscss', 'Steve Losh',
        description='''
            <p>
              A small Flask extension that makes it easy to use
              <a href=http://lesscss.org/>LessCSS</a> with your
              Flask application.
        ''',
        docs='http://sjl.bitbucket.org/flask-lesscss/',
        bitbucket='sjl/flask-lesscss'
    ),
    Extension('flask-urls', 'Steve Losh',
        description='''
            <p>
              A collection of URL-related functions for Flask applications.
        ''',
        docs='http://sjl.bitbucket.org/flask-urls/',
        bitbucket='sjl/flask-urls'
    )
]
database.sort(key=lambda x: x.name.lower())


@extensions.route('/')
def index():
    return render_template('extensions/index.html', extensions=database)


@extensions.route('/creating/')
def creating():
    return render_template('extensions/creating.html')
