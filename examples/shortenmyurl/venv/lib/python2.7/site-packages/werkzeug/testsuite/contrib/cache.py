# -*- coding: utf-8 -*-
"""
    werkzeug.testsuite.cache
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Tests the cache system

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import os
import time
import unittest
import tempfile
import shutil

from werkzeug.testsuite import WerkzeugTestCase
from werkzeug.contrib import cache

try:
    import redis
    try:
        from redis.exceptions import ConnectionError as RedisConnectionError
        cache.RedisCache(key_prefix='werkzeug-test-case:')._client.set('test','connection')
    except RedisConnectionError:
        redis = None
except ImportError:
    redis = None
try:
    import pylibmc as memcache
except ImportError:
    try:
        from google.appengine.api import memcache
    except ImportError:
        try:
            import memcache
        except ImportError:
            memcache = None


class SimpleCacheTestCase(WerkzeugTestCase):

    def test_get_dict(self):
        c = cache.SimpleCache()
        c.set('a', 'a')
        c.set('b', 'b')
        d = c.get_dict('a', 'b')
        assert 'a' in d
        assert 'a' == d['a']
        assert 'b' in d
        assert 'b' == d['b']

    def test_set_many(self):
        c = cache.SimpleCache()
        c.set_many({0: 0, 1: 1, 2: 4})
        assert c.get(2) == 4
        c.set_many((i, i*i) for i in range(3))
        assert c.get(2) == 4


class FileSystemCacheTestCase(WerkzeugTestCase):

    def test_set_get(self):
        tmp_dir = tempfile.mkdtemp()
        try:
            c = cache.FileSystemCache(cache_dir=tmp_dir)
            for i in range(3):
                c.set(str(i), i * i)
            for i in range(3):
                result = c.get(str(i))
                assert result == i * i
        finally:
            shutil.rmtree(tmp_dir)

    def test_filesystemcache_prune(self):
        THRESHOLD = 13
        tmp_dir = tempfile.mkdtemp()
        c = cache.FileSystemCache(cache_dir=tmp_dir, threshold=THRESHOLD)
        for i in range(2 * THRESHOLD):
            c.set(str(i), i)
        cache_files = os.listdir(tmp_dir)
        shutil.rmtree(tmp_dir)
        assert len(cache_files) <= THRESHOLD


    def test_filesystemcache_clear(self):
        tmp_dir = tempfile.mkdtemp()
        c = cache.FileSystemCache(cache_dir=tmp_dir)
        c.set('foo', 'bar')
        cache_files = os.listdir(tmp_dir)
        assert len(cache_files) == 1
        c.clear()
        cache_files = os.listdir(tmp_dir)
        assert len(cache_files) == 0
        shutil.rmtree(tmp_dir)


class RedisCacheTestCase(WerkzeugTestCase):

    def make_cache(self):
        return cache.RedisCache(key_prefix='werkzeug-test-case:')

    def teardown(self):
        self.make_cache().clear()

    def test_compat(self):
        c = self.make_cache()
        c._client.set(c.key_prefix + 'foo', b'Awesome')
        self.assert_equal(c.get('foo'), b'Awesome')
        c._client.set(c.key_prefix + 'foo', b'42')
        self.assert_equal(c.get('foo'), 42)

    def test_get_set(self):
        c = self.make_cache()
        c.set('foo', ['bar'])
        assert c.get('foo') == ['bar']

    def test_get_many(self):
        c = self.make_cache()
        c.set('foo', ['bar'])
        c.set('spam', 'eggs')
        assert c.get_many('foo', 'spam') == [['bar'], 'eggs']

    def test_set_many(self):
        c = self.make_cache()
        c.set_many({'foo': 'bar', 'spam': ['eggs']})
        assert c.get('foo') == 'bar'
        assert c.get('spam') == ['eggs']

    def test_expire(self):
        c = self.make_cache()
        c.set('foo', 'bar', 1)
        time.sleep(2)
        assert c.get('foo') is None

    def test_add(self):
        c = self.make_cache()
        # sanity check that add() works like set()
        c.add('foo', 'bar')
        assert c.get('foo') == 'bar'
        c.add('foo', 'qux')
        assert c.get('foo') == 'bar'

    def test_delete(self):
        c = self.make_cache()
        c.add('foo', 'bar')
        assert c.get('foo') == 'bar'
        c.delete('foo')
        assert c.get('foo') is None

    def test_delete_many(self):
        c = self.make_cache()
        c.add('foo', 'bar')
        c.add('spam', 'eggs')
        c.delete_many('foo', 'spam')
        assert c.get('foo') is None
        assert c.get('spam') is None

    def test_inc_dec(self):
        c = self.make_cache()
        c.set('foo', 1)
        self.assert_equal(c.inc('foo'), 2)
        self.assert_equal(c.dec('foo'), 1)
        c.delete('foo')

    def test_true_false(self):
        c = self.make_cache()
        c.set('foo', True)
        assert c.get('foo') == True
        c.set('bar', False)
        assert c.get('bar') == False


class MemcachedCacheTestCase(WerkzeugTestCase):

    def make_cache(self):
        return cache.MemcachedCache(key_prefix='werkzeug-test-case:')

    def teardown(self):
        self.make_cache().clear()

    def test_compat(self):
        c = self.make_cache()
        c._client.set(c.key_prefix + b'foo', 'bar')
        self.assert_equal(c.get('foo'), 'bar')

    def test_get_set(self):
        c = self.make_cache()
        c.set('foo', 'bar')
        self.assert_equal(c.get('foo'), 'bar')

    def test_get_many(self):
        c = self.make_cache()
        c.set('foo', 'bar')
        c.set('spam', 'eggs')
        self.assert_equal(c.get_many('foo', 'spam'), ['bar', 'eggs'])

    def test_set_many(self):
        c = self.make_cache()
        c.set_many({'foo': 'bar', 'spam': 'eggs'})
        self.assert_equal(c.get('foo'), 'bar')
        self.assert_equal(c.get('spam'), 'eggs')

    def test_expire(self):
        c = self.make_cache()
        c.set('foo', 'bar', 1)
        time.sleep(2)
        self.assert_is_none(c.get('foo'))

    def test_add(self):
        c = self.make_cache()
        c.add('foo', 'bar')
        self.assert_equal(c.get('foo'), 'bar')
        c.add('foo', 'baz')
        self.assert_equal(c.get('foo'), 'bar')

    def test_delete(self):
        c = self.make_cache()
        c.add('foo', 'bar')
        self.assert_equal(c.get('foo'), 'bar')
        c.delete('foo')
        self.assert_is_none(c.get('foo'))

    def test_delete_many(self):
        c = self.make_cache()
        c.add('foo', 'bar')
        c.add('spam', 'eggs')
        c.delete_many('foo', 'spam')
        self.assert_is_none(c.get('foo'))
        self.assert_is_none(c.get('spam'))

    def test_inc_dec(self):
        c = self.make_cache()
        c.set('foo', 1)
        # XXX: Is this an intended difference?
        c.inc('foo')
        self.assert_equal(c.get('foo'), 2)
        c.dec('foo')
        self.assert_equal(c.get('foo'), 1)

    def test_true_false(self):
        c = self.make_cache()
        c.set('foo', True)
        self.assert_equal(c.get('foo'), True)
        c.set('bar', False)
        self.assert_equal(c.get('bar'), False)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SimpleCacheTestCase))
    suite.addTest(unittest.makeSuite(FileSystemCacheTestCase))
    if redis is not None:
        suite.addTest(unittest.makeSuite(RedisCacheTestCase))
    if memcache is not None:
        suite.addTest(unittest.makeSuite(MemcachedCacheTestCase))
    return suite
