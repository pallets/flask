# -*- coding: utf-8 -*-
"""
    werkzeug.testsuite.utils
    ~~~~~~~~~~~~~~~~~~~~~~~~

    General utilities.

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import with_statement

import unittest
from datetime import datetime
from functools import partial

from werkzeug.testsuite import WerkzeugTestCase

from werkzeug import utils
from werkzeug.datastructures import Headers
from werkzeug.http import parse_date, http_date
from werkzeug.wrappers import BaseResponse
from werkzeug.test import Client, run_wsgi_app
from werkzeug._compat import text_type, implements_iterator


class GeneralUtilityTestCase(WerkzeugTestCase):

    def test_redirect(self):
        resp = utils.redirect(u'/füübär')
        self.assert_in(b'/f%C3%BC%C3%BCb%C3%A4r', resp.get_data())
        self.assert_equal(resp.headers['Location'], '/f%C3%BC%C3%BCb%C3%A4r')
        self.assert_equal(resp.status_code, 302)

        resp = utils.redirect(u'http://☃.net/', 307)
        self.assert_in(b'http://xn--n3h.net/', resp.get_data())
        self.assert_equal(resp.headers['Location'], 'http://xn--n3h.net/')
        self.assert_equal(resp.status_code, 307)

        resp = utils.redirect('http://example.com/', 305)
        self.assert_equal(resp.headers['Location'], 'http://example.com/')
        self.assert_equal(resp.status_code, 305)

    def test_redirect_no_unicode_header_keys(self):
        # Make sure all headers are native keys.  This was a bug at one point
        # due to an incorrect conversion.
        resp = utils.redirect('http://example.com/', 305)
        for key, value in resp.headers.items():
            self.assert_equal(type(key), str)
            self.assert_equal(type(value), text_type)
        self.assert_equal(resp.headers['Location'], 'http://example.com/')
        self.assert_equal(resp.status_code, 305)

    def test_redirect_xss(self):
        location = 'http://example.com/?xss="><script>alert(1)</script>'
        resp = utils.redirect(location)
        self.assert_not_in(b'<script>alert(1)</script>', resp.get_data())

        location = 'http://example.com/?xss="onmouseover="alert(1)'
        resp = utils.redirect(location)
        self.assert_not_in(b'href="http://example.com/?xss="onmouseover="alert(1)"', resp.get_data())

    def test_cached_property(self):
        foo = []
        class A(object):
            def prop(self):
                foo.append(42)
                return 42
            prop = utils.cached_property(prop)

        a = A()
        p = a.prop
        q = a.prop
        self.assert_true(p == q == 42)
        self.assert_equal(foo, [42])

        foo = []
        class A(object):
            def _prop(self):
                foo.append(42)
                return 42
            prop = utils.cached_property(_prop, name='prop')
            del _prop

        a = A()
        p = a.prop
        q = a.prop
        self.assert_true(p == q == 42)
        self.assert_equal(foo, [42])

    def test_environ_property(self):
        class A(object):
            environ = {'string': 'abc', 'number': '42'}

            string = utils.environ_property('string')
            missing = utils.environ_property('missing', 'spam')
            read_only = utils.environ_property('number')
            number = utils.environ_property('number', load_func=int)
            broken_number = utils.environ_property('broken_number', load_func=int)
            date = utils.environ_property('date', None, parse_date, http_date,
                                    read_only=False)
            foo = utils.environ_property('foo')

        a = A()
        self.assert_equal(a.string, 'abc')
        self.assert_equal(a.missing, 'spam')
        def test_assign():
            a.read_only = 'something'
        self.assert_raises(AttributeError, test_assign)
        self.assert_equal(a.number, 42)
        self.assert_equal(a.broken_number, None)
        self.assert_is_none(a.date)
        a.date = datetime(2008, 1, 22, 10, 0, 0, 0)
        self.assert_equal(a.environ['date'], 'Tue, 22 Jan 2008 10:00:00 GMT')

    def test_escape(self):
        class Foo(str):
            def __html__(self):
                return text_type(self)
        self.assert_equal(utils.escape(None), '')
        self.assert_equal(utils.escape(42), '42')
        self.assert_equal(utils.escape('<>'), '&lt;&gt;')
        self.assert_equal(utils.escape('"foo"'), '&quot;foo&quot;')
        self.assert_equal(utils.escape(Foo('<foo>')), '<foo>')

    def test_unescape(self):
        self.assert_equal(utils.unescape('&lt;&auml;&gt;'), u'<ä>')

    def test_run_wsgi_app(self):
        def foo(environ, start_response):
            start_response('200 OK', [('Content-Type', 'text/plain')])
            yield '1'
            yield '2'
            yield '3'

        app_iter, status, headers = run_wsgi_app(foo, {})
        self.assert_equal(status, '200 OK')
        self.assert_equal(list(headers), [('Content-Type', 'text/plain')])
        self.assert_equal(next(app_iter), '1')
        self.assert_equal(next(app_iter), '2')
        self.assert_equal(next(app_iter), '3')
        self.assert_raises(StopIteration, partial(next, app_iter))

        got_close = []
        @implements_iterator
        class CloseIter(object):
            def __init__(self):
                self.iterated = False
            def __iter__(self):
                return self
            def close(self):
                got_close.append(None)
            def __next__(self):
                if self.iterated:
                    raise StopIteration()
                self.iterated = True
                return 'bar'

        def bar(environ, start_response):
            start_response('200 OK', [('Content-Type', 'text/plain')])
            return CloseIter()

        app_iter, status, headers = run_wsgi_app(bar, {})
        self.assert_equal(status, '200 OK')
        self.assert_equal(list(headers), [('Content-Type', 'text/plain')])
        self.assert_equal(next(app_iter), 'bar')
        self.assert_raises(StopIteration, partial(next, app_iter))
        app_iter.close()

        self.assert_equal(run_wsgi_app(bar, {}, True)[0], ['bar'])

        self.assert_equal(len(got_close), 2)

    def test_import_string(self):
        import cgi
        from werkzeug.debug import DebuggedApplication
        self.assert_is(utils.import_string('cgi.escape'), cgi.escape)
        self.assert_is(utils.import_string(u'cgi.escape'), cgi.escape)
        self.assert_is(utils.import_string('cgi:escape'), cgi.escape)
        self.assert_is_none(utils.import_string('XXXXXXXXXXXX', True))
        self.assert_is_none(utils.import_string('cgi.XXXXXXXXXXXX', True))
        self.assert_is(utils.import_string(u'cgi.escape'), cgi.escape)
        self.assert_is(utils.import_string(u'werkzeug.debug.DebuggedApplication'), DebuggedApplication)
        self.assert_raises(ImportError, utils.import_string, 'XXXXXXXXXXXXXXXX')
        self.assert_raises(ImportError, utils.import_string, 'cgi.XXXXXXXXXX')

    def test_find_modules(self):
        self.assert_equal(list(utils.find_modules('werkzeug.debug')), \
            ['werkzeug.debug.console', 'werkzeug.debug.repr',
             'werkzeug.debug.tbtools'])

    def test_html_builder(self):
        html = utils.html
        xhtml = utils.xhtml
        self.assert_equal(html.p('Hello World'), '<p>Hello World</p>')
        self.assert_equal(html.a('Test', href='#'), '<a href="#">Test</a>')
        self.assert_equal(html.br(), '<br>')
        self.assert_equal(xhtml.br(), '<br />')
        self.assert_equal(html.img(src='foo'), '<img src="foo">')
        self.assert_equal(xhtml.img(src='foo'), '<img src="foo" />')
        self.assert_equal(html.html(
            html.head(
                html.title('foo'),
                html.script(type='text/javascript')
            )
        ), '<html><head><title>foo</title><script type="text/javascript">'
           '</script></head></html>')
        self.assert_equal(html('<foo>'), '&lt;foo&gt;')
        self.assert_equal(html.input(disabled=True), '<input disabled>')
        self.assert_equal(xhtml.input(disabled=True), '<input disabled="disabled" />')
        self.assert_equal(html.input(disabled=''), '<input>')
        self.assert_equal(xhtml.input(disabled=''), '<input />')
        self.assert_equal(html.input(disabled=None), '<input>')
        self.assert_equal(xhtml.input(disabled=None), '<input />')
        self.assert_equal(html.script('alert("Hello World");'), '<script>' \
            'alert("Hello World");</script>')
        self.assert_equal(xhtml.script('alert("Hello World");'), '<script>' \
            '/*<![CDATA[*/alert("Hello World");/*]]>*/</script>')

    def test_validate_arguments(self):
        take_none = lambda: None
        take_two = lambda a, b: None
        take_two_one_default = lambda a, b=0: None

        self.assert_equal(utils.validate_arguments(take_two, (1, 2,), {}), ((1, 2), {}))
        self.assert_equal(utils.validate_arguments(take_two, (1,), {'b': 2}), ((1, 2), {}))
        self.assert_equal(utils.validate_arguments(take_two_one_default, (1,), {}), ((1, 0), {}))
        self.assert_equal(utils.validate_arguments(take_two_one_default, (1, 2), {}), ((1, 2), {}))

        self.assert_raises(utils.ArgumentValidationError,
            utils.validate_arguments, take_two, (), {})

        self.assert_equal(utils.validate_arguments(take_none, (1, 2,), {'c': 3}), ((), {}))
        self.assert_raises(utils.ArgumentValidationError,
               utils.validate_arguments, take_none, (1,), {}, drop_extra=False)
        self.assert_raises(utils.ArgumentValidationError,
               utils.validate_arguments, take_none, (), {'a': 1}, drop_extra=False)

    def test_header_set_duplication_bug(self):
        headers = Headers([
            ('Content-Type', 'text/html'),
            ('Foo', 'bar'),
            ('Blub', 'blah')
        ])
        headers['blub'] = 'hehe'
        headers['blafasel'] = 'humm'
        self.assert_equal(headers, Headers([
            ('Content-Type', 'text/html'),
            ('Foo', 'bar'),
            ('blub', 'hehe'),
            ('blafasel', 'humm')
        ]))

    def test_append_slash_redirect(self):
        def app(env, sr):
            return utils.append_slash_redirect(env)(env, sr)
        client = Client(app, BaseResponse)
        response = client.get('foo', base_url='http://example.org/app')
        self.assert_equal(response.status_code, 301)
        self.assert_equal(response.headers['Location'], 'http://example.org/app/foo/')

    def test_cached_property_doc(self):
        @utils.cached_property
        def foo():
            """testing"""
            return 42
        self.assert_equal(foo.__doc__, 'testing')
        self.assert_equal(foo.__name__, 'foo')
        self.assert_equal(foo.__module__, __name__)

    def test_secure_filename(self):
        self.assert_equal(utils.secure_filename('My cool movie.mov'),
                          'My_cool_movie.mov')
        self.assert_equal(utils.secure_filename('../../../etc/passwd'),
                          'etc_passwd')
        self.assert_equal(utils.secure_filename(u'i contain cool \xfcml\xe4uts.txt'),
                          'i_contain_cool_umlauts.txt')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(GeneralUtilityTestCase))
    return suite
