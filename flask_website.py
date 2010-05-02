from __future__ import with_statement
from hashlib import md5
from werkzeug import parse_date
from flask import Flask, render_template, json, url_for, abort, Markup
from jinja2.utils import urlize
app = Flask(__name__)


THREADS_PER_PAGE = 15


class Mail(object):

    def __init__(self, d):
        self.msgid = d['msgid']
        self.author_name, self.author_addr = d['author']
        self.date = parse_date(d['date'])
        self.subject = d['subject']
        self.children = [Mail(x) for x in d['children']]
        self.text = d['text']

    @property
    def rendered_text(self):
        result = []
        in_sig = False
        for line in self.text.splitlines():
            if line == u'-- ':
              in_sig = True
            if in_sig:
                line = Markup(u'<span class=sig>%s</span>' % line)
            elif line.startswith('>'):
                line = Markup(u'<span class=quote>%s</span>' % line)
            result.append(urlize(line))
        return Markup(u'\n'.join(result))

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
            with app.open_resource('_mailinglist/threads/%s-%02d-%02d/%s' %
                                   (year, month, day, slug)) as f:
                return Thread(json.load(f))
        except IOError:
            pass

    @staticmethod
    def get_list():
        with app.open_resource('_mailinglist/threads/threadlist') as f:
            return [Thread(x) for x in json.load(f)]

    @property
    def url(self):
        return url_for('mailinglist_show_thread', year=self.date.year,
                       month=self.date.month, day=self.date.day,
                       slug=self.slug)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/mailinglist/')
def mailinglist_index():
    return render_template('mailinglist/index.html')


@app.route('/mailinglist/archive/', defaults={'page': 1})
@app.route('/mailinglist/archive/page/<int:page>/')
def mailinglist_archive(page):
    all_threads = Thread.get_list()
    offset = (page - 1) * THREADS_PER_PAGE
    threads = all_threads[offset:offset + THREADS_PER_PAGE]
    if page != 1 and not threads:
        abort(404)
    return render_template('mailinglist/archive.html',
                           page_count=len(threads) // THREADS_PER_PAGE + 1,
                           page=page, threads=threads)


@app.route('/mailinglist/archive/<int:year>/<int:month>/<int:day>/<slug>/')
def mailinglist_show_thread(year, month, day, slug):
    thread = Thread.get(year, month, day, slug)
    if thread is None:
        abort(404)
    return render_template('mailinglist/show_thread.html', thread=thread)


@app.route('/snippets/')
def snippets():
    return render_template('snippets/index.html')


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=True)
