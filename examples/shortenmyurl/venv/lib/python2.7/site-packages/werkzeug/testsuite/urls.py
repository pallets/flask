# -*- coding: utf-8 -*-
"""
    werkzeug.testsuite.urls
    ~~~~~~~~~~~~~~~~~~~~~~~

    URL helper tests.

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import unittest

from werkzeug.testsuite import WerkzeugTestCase

from werkzeug.datastructures import OrderedMultiDict
from werkzeug import urls
from werkzeug._compat import text_type, NativeStringIO, BytesIO


class URLsTestCase(WerkzeugTestCase):

    def test_replace(self):
        url = urls.url_parse('http://de.wikipedia.org/wiki/Troll')
        self.assert_strict_equal(url.replace(query='foo=bar'),
                                 urls.url_parse('http://de.wikipedia.org/wiki/Troll?foo=bar'))
        self.assert_strict_equal(url.replace(scheme='https'),
                                 urls.url_parse('https://de.wikipedia.org/wiki/Troll'))

    def test_quoting(self):
        self.assert_strict_equal(urls.url_quote(u'\xf6\xe4\xfc'), '%C3%B6%C3%A4%C3%BC')
        self.assert_strict_equal(urls.url_unquote(urls.url_quote(u'#%="\xf6')), u'#%="\xf6')
        self.assert_strict_equal(urls.url_quote_plus('foo bar'), 'foo+bar')
        self.assert_strict_equal(urls.url_unquote_plus('foo+bar'), u'foo bar')
        self.assert_strict_equal(urls.url_quote_plus('foo+bar'), 'foo%2Bbar')
        self.assert_strict_equal(urls.url_unquote_plus('foo%2Bbar'), u'foo+bar')
        self.assert_strict_equal(urls.url_encode({b'a': None, b'b': b'foo bar'}), 'b=foo+bar')
        self.assert_strict_equal(urls.url_encode({u'a': None, u'b': u'foo bar'}), 'b=foo+bar')
        self.assert_strict_equal(urls.url_fix(u'http://de.wikipedia.org/wiki/Elf (Begriffsklärung)'),
               'http://de.wikipedia.org/wiki/Elf%20(Begriffskl%C3%A4rung)')
        self.assert_strict_equal(urls.url_quote_plus(42), '42')
        self.assert_strict_equal(urls.url_quote(b'\xff'), '%FF')

    def test_bytes_unquoting(self):
        self.assert_strict_equal(urls.url_unquote(urls.url_quote(
            u'#%="\xf6', charset='latin1'), charset=None), b'#%="\xf6')

    def test_url_decoding(self):
        x = urls.url_decode(b'foo=42&bar=23&uni=H%C3%A4nsel')
        self.assert_strict_equal(x['foo'], u'42')
        self.assert_strict_equal(x['bar'], u'23')
        self.assert_strict_equal(x['uni'], u'Hänsel')

        x = urls.url_decode(b'foo=42;bar=23;uni=H%C3%A4nsel', separator=b';')
        self.assert_strict_equal(x['foo'], u'42')
        self.assert_strict_equal(x['bar'], u'23')
        self.assert_strict_equal(x['uni'], u'Hänsel')

        x = urls.url_decode(b'%C3%9Ch=H%C3%A4nsel', decode_keys=True)
        self.assert_strict_equal(x[u'Üh'], u'Hänsel')

    def test_url_bytes_decoding(self):
        x = urls.url_decode(b'foo=42&bar=23&uni=H%C3%A4nsel', charset=None)
        self.assert_strict_equal(x[b'foo'], b'42')
        self.assert_strict_equal(x[b'bar'], b'23')
        self.assert_strict_equal(x[b'uni'], u'Hänsel'.encode('utf-8'))

    def test_streamed_url_decoding(self):
        item1 = u'a' * 100000
        item2 = u'b' * 400
        string = ('a=%s&b=%s&c=%s' % (item1, item2, item2)).encode('ascii')
        gen = urls.url_decode_stream(BytesIO(string), limit=len(string),
                                     return_iterator=True)
        self.assert_strict_equal(next(gen), ('a', item1))
        self.assert_strict_equal(next(gen), ('b', item2))
        self.assert_strict_equal(next(gen), ('c', item2))
        self.assert_raises(StopIteration, lambda: next(gen))

    def test_stream_decoding_string_fails(self):
        self.assert_raises(TypeError, urls.url_decode_stream, 'testing')

    def test_url_encoding(self):
        self.assert_strict_equal(urls.url_encode({'foo': 'bar 45'}), 'foo=bar+45')
        d = {'foo': 1, 'bar': 23, 'blah': u'Hänsel'}
        self.assert_strict_equal(urls.url_encode(d, sort=True), 'bar=23&blah=H%C3%A4nsel&foo=1')
        self.assert_strict_equal(urls.url_encode(d, sort=True, separator=u';'), 'bar=23;blah=H%C3%A4nsel;foo=1')

    def test_sorted_url_encode(self):
        self.assert_strict_equal(urls.url_encode({u"a": 42, u"b": 23, 1: 1, 2: 2},
            sort=True, key=lambda i: text_type(i[0])), '1=1&2=2&a=42&b=23')
        self.assert_strict_equal(urls.url_encode({u'A': 1, u'a': 2, u'B': 3, 'b': 4}, sort=True,
                          key=lambda x: x[0].lower() + x[0]), 'A=1&a=2&B=3&b=4')

    def test_streamed_url_encoding(self):
        out = NativeStringIO()
        urls.url_encode_stream({'foo': 'bar 45'}, out)
        self.assert_strict_equal(out.getvalue(), 'foo=bar+45')

        d = {'foo': 1, 'bar': 23, 'blah': u'Hänsel'}
        out = NativeStringIO()
        urls.url_encode_stream(d, out, sort=True)
        self.assert_strict_equal(out.getvalue(), 'bar=23&blah=H%C3%A4nsel&foo=1')
        out = NativeStringIO()
        urls.url_encode_stream(d, out, sort=True, separator=u';')
        self.assert_strict_equal(out.getvalue(), 'bar=23;blah=H%C3%A4nsel;foo=1')

        gen = urls.url_encode_stream(d, sort=True)
        self.assert_strict_equal(next(gen), 'bar=23')
        self.assert_strict_equal(next(gen), 'blah=H%C3%A4nsel')
        self.assert_strict_equal(next(gen), 'foo=1')
        self.assert_raises(StopIteration, lambda: next(gen))

    def test_url_fixing(self):
        x = urls.url_fix(u'http://de.wikipedia.org/wiki/Elf (Begriffskl\xe4rung)')
        self.assert_line_equal(x, 'http://de.wikipedia.org/wiki/Elf%20(Begriffskl%C3%A4rung)')

        x = urls.url_fix("http://just.a.test/$-_.+!*'(),")
        self.assert_equal(x, "http://just.a.test/$-_.+!*'(),")

    def test_url_fixing_qs(self):
        x = urls.url_fix(b'http://example.com/?foo=%2f%2f')
        self.assert_line_equal(x, 'http://example.com/?foo=%2f%2f')

        x = urls.url_fix('http://acronyms.thefreedictionary.com/Algebraic+Methods+of+Solving+the+Schr%C3%B6dinger+Equation')
        self.assert_equal(x, 'http://acronyms.thefreedictionary.com/Algebraic+Methods+of+Solving+the+Schr%C3%B6dinger+Equation')

    def test_iri_support(self):
        self.assert_strict_equal(urls.uri_to_iri('http://xn--n3h.net/'),
                          u'http://\u2603.net/')
        self.assert_strict_equal(
            urls.uri_to_iri(b'http://%C3%BCser:p%C3%A4ssword@xn--n3h.net/p%C3%A5th'),
                            u'http://\xfcser:p\xe4ssword@\u2603.net/p\xe5th')
        self.assert_strict_equal(urls.iri_to_uri(u'http://☃.net/'), 'http://xn--n3h.net/')
        self.assert_strict_equal(
            urls.iri_to_uri(u'http://üser:pässword@☃.net/påth'),
                            'http://%C3%BCser:p%C3%A4ssword@xn--n3h.net/p%C3%A5th')

        self.assert_strict_equal(urls.uri_to_iri('http://test.com/%3Fmeh?foo=%26%2F'),
                                          u'http://test.com/%3Fmeh?foo=%26%2F')

        # this should work as well, might break on 2.4 because of a broken
        # idna codec
        self.assert_strict_equal(urls.uri_to_iri(b'/foo'), u'/foo')
        self.assert_strict_equal(urls.iri_to_uri(u'/foo'), '/foo')

        self.assert_strict_equal(urls.iri_to_uri(u'http://föö.com:8080/bam/baz'),
                          'http://xn--f-1gaa.com:8080/bam/baz')

    def test_iri_safe_conversion(self):
        self.assert_strict_equal(urls.iri_to_uri(u'magnet:?foo=bar'),
                                 'magnet:?foo=bar')
        self.assert_strict_equal(urls.iri_to_uri(u'itms-service://?foo=bar'),
                                 'itms-service:?foo=bar')
        self.assert_strict_equal(urls.iri_to_uri(u'itms-service://?foo=bar',
                                                 safe_conversion=True),
                                 'itms-service://?foo=bar')

    def test_iri_safe_quoting(self):
        uri = 'http://xn--f-1gaa.com/%2F%25?q=%C3%B6&x=%3D%25#%25'
        iri = u'http://föö.com/%2F%25?q=ö&x=%3D%25#%25'
        self.assert_strict_equal(urls.uri_to_iri(uri), iri)
        self.assert_strict_equal(urls.iri_to_uri(urls.uri_to_iri(uri)), uri)

    def test_ordered_multidict_encoding(self):
        d = OrderedMultiDict()
        d.add('foo', 1)
        d.add('foo', 2)
        d.add('foo', 3)
        d.add('bar', 0)
        d.add('foo', 4)
        self.assert_equal(urls.url_encode(d), 'foo=1&foo=2&foo=3&bar=0&foo=4')

    def test_multidict_encoding(self):
        d = OrderedMultiDict()
        d.add('2013-10-10T23:26:05.657975+0000', '2013-10-10T23:26:05.657975+0000')
        self.assert_equal(urls.url_encode(d), '2013-10-10T23%3A26%3A05.657975%2B0000=2013-10-10T23%3A26%3A05.657975%2B0000')

    def test_href(self):
        x = urls.Href('http://www.example.com/')
        self.assert_strict_equal(x(u'foo'), 'http://www.example.com/foo')
        self.assert_strict_equal(x.foo(u'bar'), 'http://www.example.com/foo/bar')
        self.assert_strict_equal(x.foo(u'bar', x=42), 'http://www.example.com/foo/bar?x=42')
        self.assert_strict_equal(x.foo(u'bar', class_=42), 'http://www.example.com/foo/bar?class=42')
        self.assert_strict_equal(x.foo(u'bar', {u'class': 42}), 'http://www.example.com/foo/bar?class=42')
        self.assert_raises(AttributeError, lambda: x.__blah__)

        x = urls.Href('blah')
        self.assert_strict_equal(x.foo(u'bar'), 'blah/foo/bar')

        self.assert_raises(TypeError, x.foo, {u"foo": 23}, x=42)

        x = urls.Href('')
        self.assert_strict_equal(x('foo'), 'foo')

    def test_href_url_join(self):
        x = urls.Href(u'test')
        self.assert_line_equal(x(u'foo:bar'), u'test/foo:bar')
        self.assert_line_equal(x(u'http://example.com/'), u'test/http://example.com/')
        self.assert_line_equal(x.a(), u'test/a')

    def test_href_past_root(self):
        base_href = urls.Href('http://www.blagga.com/1/2/3')
        self.assert_strict_equal(base_href('../foo'), 'http://www.blagga.com/1/2/foo')
        self.assert_strict_equal(base_href('../../foo'), 'http://www.blagga.com/1/foo')
        self.assert_strict_equal(base_href('../../../foo'), 'http://www.blagga.com/foo')
        self.assert_strict_equal(base_href('../../../../foo'), 'http://www.blagga.com/foo')
        self.assert_strict_equal(base_href('../../../../../foo'), 'http://www.blagga.com/foo')
        self.assert_strict_equal(base_href('../../../../../../foo'), 'http://www.blagga.com/foo')

    def test_url_unquote_plus_unicode(self):
        # was broken in 0.6
        self.assert_strict_equal(urls.url_unquote_plus(u'\x6d'), u'\x6d')
        self.assert_is(type(urls.url_unquote_plus(u'\x6d')), text_type)

    def test_quoting_of_local_urls(self):
        rv = urls.iri_to_uri(u'/foo\x8f')
        self.assert_strict_equal(rv, '/foo%C2%8F')
        self.assert_is(type(rv), str)

    def test_url_attributes(self):
        rv = urls.url_parse('http://foo%3a:bar%3a@[::1]:80/123?x=y#frag')
        self.assert_strict_equal(rv.scheme, 'http')
        self.assert_strict_equal(rv.auth, 'foo%3a:bar%3a')
        self.assert_strict_equal(rv.username, u'foo:')
        self.assert_strict_equal(rv.password, u'bar:')
        self.assert_strict_equal(rv.raw_username, 'foo%3a')
        self.assert_strict_equal(rv.raw_password, 'bar%3a')
        self.assert_strict_equal(rv.host, '::1')
        self.assert_equal(rv.port, 80)
        self.assert_strict_equal(rv.path, '/123')
        self.assert_strict_equal(rv.query, 'x=y')
        self.assert_strict_equal(rv.fragment, 'frag')

        rv = urls.url_parse(u'http://\N{SNOWMAN}.com/')
        self.assert_strict_equal(rv.host, u'\N{SNOWMAN}.com')
        self.assert_strict_equal(rv.ascii_host, 'xn--n3h.com')

    def test_url_attributes_bytes(self):
        rv = urls.url_parse(b'http://foo%3a:bar%3a@[::1]:80/123?x=y#frag')
        self.assert_strict_equal(rv.scheme, b'http')
        self.assert_strict_equal(rv.auth, b'foo%3a:bar%3a')
        self.assert_strict_equal(rv.username, u'foo:')
        self.assert_strict_equal(rv.password, u'bar:')
        self.assert_strict_equal(rv.raw_username, b'foo%3a')
        self.assert_strict_equal(rv.raw_password, b'bar%3a')
        self.assert_strict_equal(rv.host, b'::1')
        self.assert_equal(rv.port, 80)
        self.assert_strict_equal(rv.path, b'/123')
        self.assert_strict_equal(rv.query, b'x=y')
        self.assert_strict_equal(rv.fragment, b'frag')

    def test_url_joining(self):
        self.assert_strict_equal(urls.url_join('/foo', '/bar'), '/bar')
        self.assert_strict_equal(urls.url_join('http://example.com/foo', '/bar'),
                                 'http://example.com/bar')
        self.assert_strict_equal(urls.url_join('file:///tmp/', 'test.html'),
                                 'file:///tmp/test.html')
        self.assert_strict_equal(urls.url_join('file:///tmp/x', 'test.html'),
                                 'file:///tmp/test.html')
        self.assert_strict_equal(urls.url_join('file:///tmp/x', '../../../x.html'),
                                 'file:///x.html')

    def test_partial_unencoded_decode(self):
        ref = u'foo=정상처리'.encode('euc-kr')
        x = urls.url_decode(ref, charset='euc-kr')
        self.assert_strict_equal(x['foo'], u'정상처리')

    def test_iri_to_uri_idempotence_ascii_only(self):
        uri = u'http://www.idempoten.ce'
        uri = urls.iri_to_uri(uri)
        self.assert_equal(urls.iri_to_uri(uri), uri)

    def test_iri_to_uri_idempotence_non_ascii(self):
        uri = u'http://\N{SNOWMAN}/\N{SNOWMAN}'
        uri = urls.iri_to_uri(uri)
        self.assert_equal(urls.iri_to_uri(uri), uri)

    def test_uri_to_iri_idempotence_ascii_only(self):
        uri = 'http://www.idempoten.ce'
        uri = urls.uri_to_iri(uri)
        self.assert_equal(urls.uri_to_iri(uri), uri)

    def test_uri_to_iri_idempotence_non_ascii(self):
        uri = 'http://xn--n3h/%E2%98%83'
        uri = urls.uri_to_iri(uri)
        self.assert_equal(urls.uri_to_iri(uri), uri)

    def test_iri_to_uri_to_iri(self):
        iri = u'http://föö.com/'
        uri = urls.iri_to_uri(iri)
        self.assert_equal(urls.uri_to_iri(uri), iri)

    def test_uri_to_iri_to_uri(self):
        uri = 'http://xn--f-rgao.com/%C3%9E'
        iri = urls.uri_to_iri(uri)
        self.assert_equal(urls.iri_to_uri(iri), uri)

    def test_uri_iri_normalization(self):
        uri = 'http://xn--f-rgao.com/%E2%98%90/fred?utf8=%E2%9C%93'
        iri = u'http://föñ.com/\N{BALLOT BOX}/fred?utf8=\u2713'

        tests = [
            u'http://föñ.com/\N{BALLOT BOX}/fred?utf8=\u2713',
            u'http://xn--f-rgao.com/\u2610/fred?utf8=\N{CHECK MARK}',
            b'http://xn--f-rgao.com/%E2%98%90/fred?utf8=%E2%9C%93',
            u'http://xn--f-rgao.com/%E2%98%90/fred?utf8=%E2%9C%93',
            u'http://föñ.com/\u2610/fred?utf8=%E2%9C%93',
            b'http://xn--f-rgao.com/\xe2\x98\x90/fred?utf8=\xe2\x9c\x93',
        ]

        for test in tests:
            self.assert_equal(urls.uri_to_iri(test), iri)
            self.assert_equal(urls.iri_to_uri(test), uri)
            self.assert_equal(urls.uri_to_iri(urls.iri_to_uri(test)), iri)
            self.assert_equal(urls.iri_to_uri(urls.uri_to_iri(test)), uri)
            self.assert_equal(urls.uri_to_iri(urls.uri_to_iri(test)), iri)
            self.assert_equal(urls.iri_to_uri(urls.iri_to_uri(test)), uri)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(URLsTestCase))
    return suite
