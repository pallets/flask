from hashlib import md5
from flask import Markup, url_for, json
from werkzeug import parse_date, http_date
from jinja2.utils import urlize
from flask_website import app
from flask_website.utils import split_lines_wrapping


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
                      (app.config['MAILINGLIST_PATH'], year, month,
                       day, slug)) as f:
                return Thread(json.load(f))
        except IOError:
            pass

    @staticmethod
    def get_list():
        with open('%s/threads/threadlist' % app.config['MAILINGLIST_PATH']) as f:
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
