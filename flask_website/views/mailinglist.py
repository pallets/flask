from __future__ import with_statement
import os
from math import ceil
from hashlib import md5
from werkzeug import parse_date, http_date
from jinja2.utils import urlize
from flask import Module, render_template, json, url_for, abort, Markup, \
     jsonify
from flask_website.utils import split_lines_wrapping, request_wants_json
from flask_website import config

mod = Module(__name__, url_prefix='/mailinglist')


class Mail(object):

    def __init__(self, d):
        self.msgid = d['msgid']
        self.author_name, self.author_addr = d['author']
        self.date = parse_date(d['date'])
        self.subject = d['subject']
        self.children = [Mail(x) for x in d['children']]
        self.text = d['text']

    def rendered_text(self):
        result = []
        in_sig = False
        for line in split_lines_wrapping(self.text):
            if line == u'-- ':
                in_sig = True
            # the extra space at the end is a simple workaround for
            # urlize not to consume the </span> as part of the URL
            if in_sig:
                line = Markup(u'<span class=sig>%s </span>') % line
            elif line.startswith('>'):
                line = Markup(u'<span class=quote>%s </span>') % line
            result.append(urlize(line))
        return Markup(u'\n'.join(result))

    def to_json(self):
        rv = vars(self).copy()
        rv.pop('author_email', None)
        rv['date'] = http_date(rv['date'])
        rv['children'] = [c.to_json() for c in rv['children']]
        return rv

    @property
    def id(self):
        return md5(self.msgid.encode('utf-8')).hexdigest()


class Thread(object):

    def __init__(self, d):
        self.slug = d['slug'].rsplit('/', 1)[-1]
        self.title = d['title']
        self.reply_count = d['reply_count']
        self.author_name, self.author_email = d['author']
        self.date = parse_date(d['date'])
        if 'root' in d:
            self.root = Mail(d['root'])

    @staticmethod
    def get(year, month, day, slug):
        try:
            with open('%s/threads/%s-%02d-%02d/%s' %
                      (config.MAILINGLIST_PATH, year, month, day, slug)) as f:
                return Thread(json.load(f))
        except IOError:
            pass

    @staticmethod
    def get_list():
        with open('%s/threads/threadlist' % config.MAILINGLIST_PATH) as f:
            return [Thread(x) for x in json.load(f)]

    @property
    def url(self):
        return url_for('mailinglist.show_thread', year=self.date.year,
                       month=self.date.month, day=self.date.day,
                       slug=self.slug)

    def to_json(self):
        rv = vars(self).copy()
        rv['date'] = http_date(rv['date'])
        if 'root' in rv:
            rv['root'] = rv['root'].to_json()
        return rv


@mod.route('/')
def index():
    return render_template('mailinglist/index.html')


@mod.route('/archive/', defaults={'page': 1})
@mod.route('/archive/page/<int:page>/')
def archive(page):
    all_threads = Thread.get_list()
    offset = (page - 1) * config.THREADS_PER_PAGE
    threads = all_threads[offset:offset + config.THREADS_PER_PAGE]
    if page != 1 and not threads:
        abort(404)
    page_count = int(ceil(len(all_threads) // float(config.THREADS_PER_PAGE)))
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
