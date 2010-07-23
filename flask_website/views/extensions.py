from flask import Module, render_template, jsonify, request
from flask_website.listings.extensions import extensions

mod = Module(__name__, url_prefix='/extensions')


def wants_json():
    return request.accept_mimetypes \
        .best_match(['application/json', 'text/html']) == 'application/json'

@mod.route('/')
def index():
    if wants_json():
        return jsonify(extensions=map(vars, extensions))
    return render_template('extensions/index.html', extensions=extensions)


@mod.route('/creating/')
def creating():
    return render_template('extensions/creating.html')
