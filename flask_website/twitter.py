from __future__ import with_statement
import urllib2
import time
import threading
from flask import json, Markup
from werkzeug import url_encode, parse_date, http_date


class SearchResult(object):

    def __init__(self, result):
        self.text = Markup(result['text']).unescape()
        self.user = result['from_user']
        self.via = Markup(Markup(result['source']).unescape())
        self.pub_date = parse_date(result['created_at'])
        self.profile_image = result['profile_image_url']
        self.type = result['metadata']['result_type']
        self.retweets = result['metadata'].get('recent_retweets') or 0

    def to_json(self):
        rv = vars(self).copy()
        rv['pub_date'] = http_date(rv['pub_date'])
        rv['via'] = unicode(rv['via'])
        return rv


class SearchQuery(object):
    fetch_timeout = 10

    def __init__(self, required=None, optional=None, timeout=60, lang=None):
        self.required = set(x.lower() for x in (required or ()))
        self.optional = set(x.lower() for x in (optional or ()))
        self.lang = lang
        self.timeout = timeout
        self._last_fetch = 0
        self._last_scheduled_fetch = 0
        self._cached = None

    @property
    def query(self):
        def _quote_if(x):
            if len(x.split()) != 1:
                return u'"%s"' % x
            return x
        q = u' '.join(map(_quote_if, self.required))
        q += u' ' + u' OR '.join(map(_quote_if, self.optional))
        return q

    @property
    def feed_url(self):
        return self.get_url(kind='atom')

    def get_url(self, kind='json'):
        return 'http://search.twitter.com/search.%s?%s' % (kind, url_encode({
            'q':            self.query,
            'result_type':  'mixed',
            'rpp':          30,
            'lang':         self.lang
        }))

    def fetch(self):
        def _accept(text):
            text = text.lower()
            for word in self.required:
                if word not in text:
                    return False
            for word in self.optional:
                if word in text:
                    return True
            return False
        rv = json.load(urllib2.urlopen(self.get_url()))
        return [SearchResult(x) for x in rv['results'] if
                _accept(x['from_user'] + u': ' + x['text'])]

    @property
    def up_to_date(self):
        return time.time() < self._last_fetch + self.timeout

    def _try_refresh(self):
        if self.up_to_date:
            return
        if time.time() > self._last_scheduled_fetch + self.fetch_timeout:
            self._last_scheduled_fetch = time.time()
            threading.Thread(target=self._fetch_and_store).start()

    def _fetch_and_store(self):
        self._cached = self.fetch()
        self._last_fetch = time.time()

    def __len__(self):
        self._try_refresh()
        return len(self._cached or ())

    def __iter__(self):
        return iter(self.get())

    def get(self, limit=None):
        self._try_refresh()
        seq = (self._cached or ())
        if limit is not None:
            seq = seq[:limit]
        return seq


flask_tweets = SearchQuery(
    required=['flask'],
    optional=['code', 'dev', 'python', 'py', 'pocoo', 'micro',
              'mitsuhiko', 'framework', 'django', 'jinja', 'werkzeug',
              'documentation', 'app']
)
