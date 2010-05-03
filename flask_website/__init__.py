from flask import Flask, session, g, render_template

import websiteconfig as config

app = Flask(__name__)
app.debug = config.DEBUG
app.secret_key = config.SECRET_KEY

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.before_request
def load_currrent_user():
    g.user = User.query.filter_by(openid=session['openid']).first() \
        if 'openid' in session else None

from flask_website.views.general import general
from flask_website.views.mailinglist import mailinglist
from flask_website.views.snippets import snippets
app.register_module(general)
app.register_module(mailinglist)
app.register_module(snippets)

from flask_website.database import User
