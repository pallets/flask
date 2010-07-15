from flask import Module, render_template
from flask_website.listings.extensions import extensions

mod = Module(__name__, url_prefix='/extensions')


@mod.route('/')
def index():
    return render_template('extensions/index.html', extensions=extensions)


@mod.route('/creating/')
def creating():
    return render_template('extensions/creating.html')
