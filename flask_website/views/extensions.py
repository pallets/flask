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
    Extension('Flask-XML-RPC', 'Matthew Frazier',
        description='''
            <p>Adds <a href="http://www.xmlrpc.com/">XML-RPC</a> support to Flask.
        ''',
        bitbucket='leafstorm/flask-xml-rpc',
        docs='http://packages.python.org/Flask-XML-RPC/'
    )
]
database.sort(key=lambda x: x.name.lower())


@extensions.route('/')
def index():
    return render_template('extensions/index.html', extensions=database)


@extensions.route('/creating/')
def creating():
    return render_template('extensions/creating.html')
