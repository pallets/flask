from __future__ import with_statement
from math import ceil
from flask import Blueprint, render_template, abort, jsonify
from flask_website import app
from flask_website.utils import request_wants_json
from flask_website.mailinglist import Thread


mod = Blueprint('mailinglist', __name__, url_prefix='/mailinglist')


@mod.route('/')
def index():
    return render_template('mailinglist/index.html')


@mod.route('/archive/', defaults={'page': 1})
@mod.route('/archive/page/<int:page>/')
def archive(page):
    all_threads = Thread.get_list()
    offset = (page - 1) * app.config['THREADS_PER_PAGE']
    threads = all_threads[offset:offset + app.config['THREADS_PER_PAGE']]
    if page != 1 and not threads:
        abort(404)
    page_count = int(ceil(len(all_threads) // float(app.config['THREADS_PER_PAGE'])))
    if request_wants_json():
        return jsonify(offset=offset,
                       total=len(all_threads),
                       threads=[x.to_json() for x in threads])
    return render_template('mailinglist/archive.html',
                           page_count=page_count, page=page, threads=threads)


@mod.route('/archive/<int:year>/<int:month>/<int:day>/<slug>/')
def show_thread(year, month, day, slug):
    thread = Thread.get(year, month, day, slug)
    if thread is None:
        abort(404)
    if request_wants_json():
        return jsonify(thread=thread.to_json())
    return render_template('mailinglist/show_thread.html', thread=thread)
