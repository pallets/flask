from hashids import Hashids
import redis
import random
import config
import time
from flask import request
import urlparse
import math

import os


class UrlShortener:
    def __init__(self):
        url = urlparse.urlparse(os.environ.get('REDISCLOUD_URL'))
        self.redis = redis.Redis(host=url.hostname, port=url.port, password=url.password)

    def shortcode(self, url):
        hashids = Hashids(min_length=5)
        randomno = self.randomuniquegenerator()
        hashid = hashids.encrypt(randomno)
        return hashid

    def randomuniquegenerator(self):
        tm=int (math.floor(time.time()/10000))
        randomno=random.randrange(100000,999999)
        if randomno > tm:
            return randomno - tm
        else:
            return tm -randomno


    def addUrl(self, url):
        hashid = self.shortcode(url)
        
        if(not self.redis.exists(hashid)):
            self.redis.set(hashid,url)
            return hashid
        else:
            return self.addUrl(url)

    def shortLookup(self, hashid):
        try:
            return self.redis.get(hashid)
        except:
            return None


