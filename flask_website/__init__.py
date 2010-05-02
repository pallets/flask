from flask import Flask, render_template

import websiteconfig as config

app = Flask(__name__)
app.debug = config.DEBUG

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

from flask_website.views.general import general
from flask_website.views.mailinglist import mailinglist
from flask_website.views.snippets import snippets
app.register_module(general)
app.register_module(mailinglist)
app.register_module(snippets)
