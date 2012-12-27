from __future__ import with_statement
import urllib2
import time
import threading
import re
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
        self.original_tweeter = result['original_tweeter']
        self.retweeted_by = result['retweeted_by']

    def to_json(self):
        rv = vars(self).copy()
        rv['pub_date'] = http_date(rv['pub_date'])
        rv['via'] = unicode(rv['via'])
        return rv


class SearchQuery(object):
    fetch_timeout = 10
    
    tweeters_pattern = re.compile('(?P<rt>RT @(?P<rt_name>[\w_]+)\:)+')
    
    def __init__(self, required=(), optional=(), timeout=60, lang=None):
        self.required = set(x.lower() for x in required)
        self.optional = set(x.lower() for x in optional)
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

    def parse_tweet(self, tweet):
        """
        Takes a tweet and returns a dictionary containing the user, tweet's text, tweet's id and list of user who tweeted this tweet
        """
        text = tweet['text']
        """
        here rt would be a list of 2-tuples like ('RT @lovesh_h:', 'lovesh_h') where the last tuple would be the original tweeter of the tweet
        """
        rt = self.tweeters_pattern.findall(text)
        tweet_text_only = text
        for i in rt:
            tweet_text_only = tweet_text_only.replace(i[0], '')
        tweet_text_only = tweet_text_only.strip()
        result = {}
        result['text'] = tweet_text_only
        if len(rt) > 0:
            result['original_tweeter'] = rt[-1][1]
            result['retweeted_by'] = set(i[1] for i in rt[:-1]) 
            result['retweeted_by'].add(tweet['from_user'])     
        else:
            result['original_tweeter'] = tweet['from_user']
            result['retweeted_by'] = set()
        result['from_user'] = tweet['from_user']
        result['id_str'] = tweet['id_str']
        result['source'] = tweet['source']
        result['created_at'] = tweet['created_at']
        result['profile_image_url'] = tweet['profile_image_url']
        result['metadata'] = tweet['metadata']
        return result
        
    
    def get_unique_tweets(self, tweets):
        """
        2 tweets are considered to have same text if the text of one tweet is exactly similar to the other's text
        Take a list of tweets and returns list of tweets with each element as a dictionary with keys as tweet's text, retweeters,
        source, from_user, etc 
        
        """
        parsed_tweets = [self.parse_tweet(tweet) for tweet in tweets]
        unique_tweets = {}
        for pt in parsed_tweets:
            tweet_text = pt['text']
            if tweet_text not in unique_tweets:
                unique_tweets[tweet_text] = pt
            else:
                unique_tweets[tweet_text]['retweeted_by'].update(pt['retweeted_by'])
                
                if unique_tweets[tweet_text]['original_tweeter'] != pt['original_tweeter']:
                    """
                    In case 2 tweeters tweeted the same text without retweeting each other's tweet
                    """
                    unique_tweets[tweet_text]['retweeted_by'].add(pt['original_tweeter'])
            
        return unique_tweets.values()
        
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
        unique_tweets = self.get_unique_tweets(rv['results'])
        return [SearchResult(x) for x in unique_tweets if
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
              'documentation', 'app',
              'rest', 'api']
)
