# -*- coding: utf-8 -*-
"""
    werkzeug.testsuite.http
    ~~~~~~~~~~~~~~~~~~~~~~~

    HTTP parsing utilities.

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import unittest
from datetime import datetime

from werkzeug.testsuite import WerkzeugTestCase
from werkzeug._compat import itervalues, wsgi_encoding_dance

from werkzeug import http, datastructures
from werkzeug.test import create_environ


class HTTPUtilityTestCase(WerkzeugTestCase):

    def test_accept(self):
        a = http.parse_accept_header('en-us,ru;q=0.5')
        self.assert_equal(list(itervalues(a)), ['en-us', 'ru'])
        self.assert_equal(a.best, 'en-us')
        self.assert_equal(a.find('ru'), 1)
        self.assert_raises(ValueError, a.index, 'de')
        self.assert_equal(a.to_header(), 'en-us,ru;q=0.5')

    def test_mime_accept(self):
        a = http.parse_accept_header('text/xml,application/xml,'
                                     'application/xhtml+xml,'
                                     'text/html;q=0.9,text/plain;q=0.8,'
                                     'image/png,*/*;q=0.5',
                                     datastructures.MIMEAccept)
        self.assert_raises(ValueError, lambda: a['missing'])
        self.assert_equal(a['image/png'],  1)
        self.assert_equal(a['text/plain'],  0.8)
        self.assert_equal(a['foo/bar'],  0.5)
        self.assert_equal(a[a.find('foo/bar')],  ('*/*', 0.5))

    def test_accept_matches(self):
        a = http.parse_accept_header('text/xml,application/xml,application/xhtml+xml,'
                                    'text/html;q=0.9,text/plain;q=0.8,'
                                    'image/png', datastructures.MIMEAccept)
        self.assert_equal(a.best_match(['text/html', 'application/xhtml+xml']),
                          'application/xhtml+xml')
        self.assert_equal(a.best_match(['text/html']),  'text/html')
        self.assert_true(a.best_match(['foo/bar']) is None)
        self.assert_equal(a.best_match(['foo/bar', 'bar/foo'],
                          default='foo/bar'),  'foo/bar')
        self.assert_equal(a.best_match(['application/xml', 'text/xml']),  'application/xml')

    def test_charset_accept(self):
        a = http.parse_accept_header('ISO-8859-1,utf-8;q=0.7,*;q=0.7',
                                     datastructures.CharsetAccept)
        self.assert_equal(a['iso-8859-1'], a['iso8859-1'])
        self.assert_equal(a['iso-8859-1'], 1)
        self.assert_equal(a['UTF8'], 0.7)
        self.assert_equal(a['ebcdic'], 0.7)

    def test_language_accept(self):
        a = http.parse_accept_header('de-AT,de;q=0.8,en;q=0.5',
                                     datastructures.LanguageAccept)
        self.assert_equal(a.best,  'de-AT')
        self.assert_true('de_AT' in a)
        self.assert_true('en' in a)
        self.assert_equal(a['de-at'], 1)
        self.assert_equal(a['en'], 0.5)

    def test_set_header(self):
        hs = http.parse_set_header('foo, Bar, "Blah baz", Hehe')
        self.assert_true('blah baz' in hs)
        self.assert_true('foobar' not in hs)
        self.assert_true('foo' in hs)
        self.assert_equal(list(hs), ['foo', 'Bar', 'Blah baz', 'Hehe'])
        hs.add('Foo')
        self.assert_equal(hs.to_header(), 'foo, Bar, "Blah baz", Hehe')

    def test_list_header(self):
        hl = http.parse_list_header('foo baz, blah')
        self.assert_equal(hl, ['foo baz', 'blah'])

    def test_dict_header(self):
        d = http.parse_dict_header('foo="bar baz", blah=42')
        self.assert_equal(d, {'foo': 'bar baz', 'blah': '42'})

    def test_cache_control_header(self):
        cc = http.parse_cache_control_header('max-age=0, no-cache')
        assert cc.max_age == 0
        assert cc.no_cache
        cc = http.parse_cache_control_header('private, community="UCI"', None,
                                             datastructures.ResponseCacheControl)
        assert cc.private
        assert cc['community'] == 'UCI'

        c = datastructures.ResponseCacheControl()
        assert c.no_cache is None
        assert c.private is None
        c.no_cache = True
        assert c.no_cache == '*'
        c.private = True
        assert c.private == '*'
        del c.private
        assert c.private is None
        assert c.to_header() == 'no-cache'

    def test_authorization_header(self):
        a = http.parse_authorization_header('Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ==')
        assert a.type == 'basic'
        assert a.username == 'Aladdin'
        assert a.password == 'open sesame'

        a = http.parse_authorization_header('''Digest username="Mufasa",
                     realm="testrealm@host.invalid",
                     nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093",
                     uri="/dir/index.html",
                     qop=auth,
                     nc=00000001,
                     cnonce="0a4f113b",
                     response="6629fae49393a05397450978507c4ef1",
                     opaque="5ccc069c403ebaf9f0171e9517f40e41"''')
        assert a.type == 'digest'
        assert a.username == 'Mufasa'
        assert a.realm == 'testrealm@host.invalid'
        assert a.nonce == 'dcd98b7102dd2f0e8b11d0f600bfb0c093'
        assert a.uri == '/dir/index.html'
        assert 'auth' in a.qop
        assert a.nc == '00000001'
        assert a.cnonce == '0a4f113b'
        assert a.response == '6629fae49393a05397450978507c4ef1'
        assert a.opaque == '5ccc069c403ebaf9f0171e9517f40e41'

        a = http.parse_authorization_header('''Digest username="Mufasa",
                     realm="testrealm@host.invalid",
                     nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093",
                     uri="/dir/index.html",
                     response="e257afa1414a3340d93d30955171dd0e",
                     opaque="5ccc069c403ebaf9f0171e9517f40e41"''')
        assert a.type == 'digest'
        assert a.username == 'Mufasa'
        assert a.realm == 'testrealm@host.invalid'
        assert a.nonce == 'dcd98b7102dd2f0e8b11d0f600bfb0c093'
        assert a.uri == '/dir/index.html'
        assert a.response == 'e257afa1414a3340d93d30955171dd0e'
        assert a.opaque == '5ccc069c403ebaf9f0171e9517f40e41'

        assert http.parse_authorization_header('') is None
        assert http.parse_authorization_header(None) is None
        assert http.parse_authorization_header('foo') is None

    def test_www_authenticate_header(self):
        wa = http.parse_www_authenticate_header('Basic realm="WallyWorld"')
        assert wa.type == 'basic'
        assert wa.realm == 'WallyWorld'
        wa.realm = 'Foo Bar'
        assert wa.to_header() == 'Basic realm="Foo Bar"'

        wa = http.parse_www_authenticate_header('''Digest
                     realm="testrealm@host.com",
                     qop="auth,auth-int",
                     nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093",
                     opaque="5ccc069c403ebaf9f0171e9517f40e41"''')
        assert wa.type == 'digest'
        assert wa.realm == 'testrealm@host.com'
        assert 'auth' in wa.qop
        assert 'auth-int' in wa.qop
        assert wa.nonce == 'dcd98b7102dd2f0e8b11d0f600bfb0c093'
        assert wa.opaque == '5ccc069c403ebaf9f0171e9517f40e41'

        wa = http.parse_www_authenticate_header('broken')
        assert wa.type == 'broken'

        assert not http.parse_www_authenticate_header('').type
        assert not http.parse_www_authenticate_header('')

    def test_etags(self):
        assert http.quote_etag('foo') == '"foo"'
        assert http.quote_etag('foo', True) == 'w/"foo"'
        assert http.unquote_etag('"foo"') == ('foo', False)
        assert http.unquote_etag('w/"foo"') == ('foo', True)
        es = http.parse_etags('"foo", "bar", w/"baz", blar')
        assert sorted(es) == ['bar', 'blar', 'foo']
        assert 'foo' in es
        assert 'baz' not in es
        assert es.contains_weak('baz')
        assert 'blar' in es
        assert es.contains_raw('w/"baz"')
        assert es.contains_raw('"foo"')
        assert sorted(es.to_header().split(', ')) == ['"bar"', '"blar"', '"foo"', 'w/"baz"']

    def test_etags_nonzero(self):
        etags = http.parse_etags('w/"foo"')
        self.assert_true(bool(etags))
        self.assert_true(etags.contains_raw('w/"foo"'))

    def test_parse_date(self):
        assert http.parse_date('Sun, 06 Nov 1994 08:49:37 GMT    ') == datetime(1994, 11, 6, 8, 49, 37)
        assert http.parse_date('Sunday, 06-Nov-94 08:49:37 GMT') == datetime(1994, 11, 6, 8, 49, 37)
        assert http.parse_date(' Sun Nov  6 08:49:37 1994') == datetime(1994, 11, 6, 8, 49, 37)
        assert http.parse_date('foo') is None

    def test_parse_date_overflows(self):
        assert http.parse_date(' Sun 02 Feb 1343 08:49:37 GMT') == datetime(1343, 2, 2, 8, 49, 37)
        assert http.parse_date('Thu, 01 Jan 1970 00:00:00 GMT') == datetime(1970, 1, 1, 0, 0)
        assert http.parse_date('Thu, 33 Jan 1970 00:00:00 GMT') is None

    def test_remove_entity_headers(self):
        now = http.http_date()
        headers1 = [('Date', now), ('Content-Type', 'text/html'), ('Content-Length', '0')]
        headers2 = datastructures.Headers(headers1)

        http.remove_entity_headers(headers1)
        assert headers1 == [('Date', now)]

        http.remove_entity_headers(headers2)
        self.assert_equal(headers2, datastructures.Headers([(u'Date', now)]))

    def test_remove_hop_by_hop_headers(self):
        headers1 = [('Connection', 'closed'), ('Foo', 'bar'),
                    ('Keep-Alive', 'wtf')]
        headers2 = datastructures.Headers(headers1)

        http.remove_hop_by_hop_headers(headers1)
        assert headers1 == [('Foo', 'bar')]

        http.remove_hop_by_hop_headers(headers2)
        assert headers2 == datastructures.Headers([('Foo', 'bar')])

    def test_parse_options_header(self):
        assert http.parse_options_header(r'something; foo="other\"thing"') == \
            ('something', {'foo': 'other"thing'})
        assert http.parse_options_header(r'something; foo="other\"thing"; meh=42') == \
            ('something', {'foo': 'other"thing', 'meh': '42'})
        assert http.parse_options_header(r'something; foo="other\"thing"; meh=42; bleh') == \
            ('something', {'foo': 'other"thing', 'meh': '42', 'bleh': None})
        assert http.parse_options_header('something; foo="other;thing"; meh=42; bleh') == \
            ('something', {'foo': 'other;thing', 'meh': '42', 'bleh': None})
        assert http.parse_options_header('something; foo="otherthing"; meh=; bleh') == \
            ('something', {'foo': 'otherthing', 'meh': None, 'bleh': None})



    def test_dump_options_header(self):
        assert http.dump_options_header('foo', {'bar': 42}) == \
            'foo; bar=42'
        assert http.dump_options_header('foo', {'bar': 42, 'fizz': None}) in \
            ('foo; bar=42; fizz', 'foo; fizz; bar=42')

    def test_dump_header(self):
        assert http.dump_header([1, 2, 3]) == '1, 2, 3'
        assert http.dump_header([1, 2, 3], allow_token=False) == '"1", "2", "3"'
        assert http.dump_header({'foo': 'bar'}, allow_token=False) == 'foo="bar"'
        assert http.dump_header({'foo': 'bar'}) == 'foo=bar'

    def test_is_resource_modified(self):
        env = create_environ()

        # ignore POST
        env['REQUEST_METHOD'] = 'POST'
        assert not http.is_resource_modified(env, etag='testing')
        env['REQUEST_METHOD'] = 'GET'

        # etagify from data
        self.assert_raises(TypeError, http.is_resource_modified, env,
                           data='42', etag='23')
        env['HTTP_IF_NONE_MATCH'] = http.generate_etag(b'awesome')
        assert not http.is_resource_modified(env, data=b'awesome')

        env['HTTP_IF_MODIFIED_SINCE'] = http.http_date(datetime(2008, 1, 1, 12, 30))
        assert not http.is_resource_modified(env,
            last_modified=datetime(2008, 1, 1, 12, 00))
        assert http.is_resource_modified(env,
            last_modified=datetime(2008, 1, 1, 13, 00))

    def test_date_formatting(self):
        assert http.cookie_date(0) == 'Thu, 01-Jan-1970 00:00:00 GMT'
        assert http.cookie_date(datetime(1970, 1, 1)) == 'Thu, 01-Jan-1970 00:00:00 GMT'
        assert http.http_date(0) == 'Thu, 01 Jan 1970 00:00:00 GMT'
        assert http.http_date(datetime(1970, 1, 1)) == 'Thu, 01 Jan 1970 00:00:00 GMT'

    def test_cookies(self):
        self.assert_strict_equal(
            dict(http.parse_cookie('dismiss-top=6; CP=null*; PHPSESSID=0a539d42abc001cd'
                              'c762809248d4beed; a=42; b="\\\";"')),
            {
                'CP':           u'null*',
                'PHPSESSID':    u'0a539d42abc001cdc762809248d4beed',
                'a':            u'42',
                'dismiss-top':  u'6',
                'b':            u'\";'
            }
        )
        self.assert_strict_equal(
            set(http.dump_cookie('foo', 'bar baz blub', 360, httponly=True,
                                 sync_expires=False).split(u'; ')),
            set([u'HttpOnly', u'Max-Age=360', u'Path=/', u'foo="bar baz blub"'])
        )
        self.assert_strict_equal(dict(http.parse_cookie('fo234{=bar; blub=Blah')),
                                 {'fo234{': u'bar', 'blub': u'Blah'})

    def test_cookie_quoting(self):
        val = http.dump_cookie("foo", "?foo")
        self.assert_strict_equal(val, 'foo="?foo"; Path=/')
        self.assert_strict_equal(dict(http.parse_cookie(val)), {'foo': u'?foo'})

        self.assert_strict_equal(dict(http.parse_cookie(r'foo="foo\054bar"')),
                                 {'foo': u'foo,bar'})

    def test_cookie_domain_resolving(self):
        val = http.dump_cookie('foo', 'bar', domain=u'\N{SNOWMAN}.com')
        self.assert_strict_equal(val, 'foo=bar; Domain=xn--n3h.com; Path=/')

    def test_cookie_unicode_dumping(self):
        val = http.dump_cookie('foo', u'\N{SNOWMAN}')
        h = datastructures.Headers()
        h.add('Set-Cookie', val)
        self.assert_equal(h['Set-Cookie'], 'foo="\\342\\230\\203"; Path=/')

        cookies = http.parse_cookie(h['Set-Cookie'])
        self.assert_equal(cookies['foo'], u'\N{SNOWMAN}')

    def test_cookie_unicode_keys(self):
        # Yes, this is technically against the spec but happens
        val = http.dump_cookie(u'fö', u'fö')
        self.assert_equal(val, wsgi_encoding_dance(u'fö="f\\303\\266"; Path=/', 'utf-8'))
        cookies = http.parse_cookie(val)
        self.assert_equal(cookies[u'fö'], u'fö')

    def test_cookie_unicode_parsing(self):
        # This is actually a correct test.  This is what is being submitted
        # by firefox if you set an unicode cookie and we get the cookie sent
        # in on Python 3 under PEP 3333.
        cookies = http.parse_cookie(u'fÃ¶=fÃ¶')
        self.assert_equal(cookies[u'fö'], u'fö')

    def test_cookie_domain_encoding(self):
        val = http.dump_cookie('foo', 'bar', domain=u'\N{SNOWMAN}.com')
        self.assert_strict_equal(val, 'foo=bar; Domain=xn--n3h.com; Path=/')

        val = http.dump_cookie('foo', 'bar', domain=u'.\N{SNOWMAN}.com')
        self.assert_strict_equal(val, 'foo=bar; Domain=.xn--n3h.com; Path=/')

        val = http.dump_cookie('foo', 'bar', domain=u'.foo.com')
        self.assert_strict_equal(val, 'foo=bar; Domain=.foo.com; Path=/')


class RangeTestCase(WerkzeugTestCase):

    def test_if_range_parsing(self):
        rv = http.parse_if_range_header('"Test"')
        assert rv.etag == 'Test'
        assert rv.date is None
        assert rv.to_header() == '"Test"'

        # weak information is dropped
        rv = http.parse_if_range_header('w/"Test"')
        assert rv.etag == 'Test'
        assert rv.date is None
        assert rv.to_header() == '"Test"'

        # broken etags are supported too
        rv = http.parse_if_range_header('bullshit')
        assert rv.etag == 'bullshit'
        assert rv.date is None
        assert rv.to_header() == '"bullshit"'

        rv = http.parse_if_range_header('Thu, 01 Jan 1970 00:00:00 GMT')
        assert rv.etag is None
        assert rv.date == datetime(1970, 1, 1)
        assert rv.to_header() == 'Thu, 01 Jan 1970 00:00:00 GMT'

        for x in '', None:
            rv = http.parse_if_range_header(x)
            assert rv.etag is None
            assert rv.date is None
            assert rv.to_header() == ''

    def test_range_parsing():
        rv = http.parse_range_header('bytes=52')
        assert rv is None

        rv = http.parse_range_header('bytes=52-')
        assert rv.units == 'bytes'
        assert rv.ranges == [(52, None)]
        assert rv.to_header() == 'bytes=52-'

        rv = http.parse_range_header('bytes=52-99')
        assert rv.units == 'bytes'
        assert rv.ranges == [(52, 100)]
        assert rv.to_header() == 'bytes=52-99'

        rv = http.parse_range_header('bytes=52-99,-1000')
        assert rv.units == 'bytes'
        assert rv.ranges == [(52, 100), (-1000, None)]
        assert rv.to_header() == 'bytes=52-99,-1000'

        rv = http.parse_range_header('bytes = 1 - 100')
        assert rv.units == 'bytes'
        assert rv.ranges == [(1, 101)]
        assert rv.to_header() == 'bytes=1-100'

        rv = http.parse_range_header('AWesomes=0-999')
        assert rv.units == 'awesomes'
        assert rv.ranges == [(0, 1000)]
        assert rv.to_header() == 'awesomes=0-999'

    def test_content_range_parsing():
        rv = http.parse_content_range_header('bytes 0-98/*')
        assert rv.units == 'bytes'
        assert rv.start == 0
        assert rv.stop == 99
        assert rv.length is None
        assert rv.to_header() == 'bytes 0-98/*'

        rv = http.parse_content_range_header('bytes 0-98/*asdfsa')
        assert rv is None

        rv = http.parse_content_range_header('bytes 0-99/100')
        assert rv.to_header() == 'bytes 0-99/100'
        rv.start = None
        rv.stop = None
        assert rv.units == 'bytes'
        assert rv.to_header() == 'bytes */100'

        rv = http.parse_content_range_header('bytes */100')
        assert rv.start is None
        assert rv.stop is None
        assert rv.length == 100
        assert rv.units == 'bytes'


class RegressionTestCase(WerkzeugTestCase):

    def test_best_match_works(self):
        # was a bug in 0.6
        rv = http.parse_accept_header('foo=,application/xml,application/xhtml+xml,'
                                     'text/html;q=0.9,text/plain;q=0.8,'
                                     'image/png,*/*;q=0.5',
                                     datastructures.MIMEAccept).best_match(['foo/bar'])
        self.assert_equal(rv, 'foo/bar')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(HTTPUtilityTestCase))
    suite.addTest(unittest.makeSuite(RegressionTestCase))
    return suite
