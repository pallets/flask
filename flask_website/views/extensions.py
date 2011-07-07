from flask import Blueprint, render_template, jsonify, redirect, \
     url_for
from flask_website.utils import request_wants_json
from flask_website.listings.extensions import extensions, unlisted

mod = Blueprint('extensions', __name__, url_prefix='/extensions')


@mod.route('/')
def index():
    if request_wants_json():
        return jsonify(extensions=[ext.to_json() for ext in extensions],
                       unlisted_extensions=[ext.to_json() for ext in unlisted])
    return render_template('extensions/index.html', extensions=extensions)


@mod.route('/creating/')
def creating():
    return redirect(url_for('docs.show', page='extensiondev'), 301)
