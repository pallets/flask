# -*- coding: utf-8 -*-
"""
    werkzeug.testsuite.test
    ~~~~~~~~~~~~~~~~~~~~~~~

    Tests the testing tools.

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import with_statement

import sys
import unittest
from io import BytesIO
from werkzeug._compat import iteritems, to_bytes

from werkzeug.testsuite import WerkzeugTestCase

from werkzeug.wrappers import Request, Response, BaseResponse
from werkzeug.test import Client, EnvironBuilder, create_environ, \
    ClientRedirectError, stream_encode_multipart, run_wsgi_app
from werkzeug.utils import redirect
from werkzeug.formparser import parse_form_data
from werkzeug.datastructures import MultiDict, FileStorage


def cookie_app(environ, start_response):
    """A WSGI application which sets a cookie, and returns as a ersponse any
    cookie which exists.
    """
    response = Response(environ.get('HTTP_COOKIE', 'No Cookie'),
                        mimetype='text/plain')
    response.set_cookie('test', 'test')
    return response(environ, start_response)


def redirect_loop_app(environ, start_response):
    response = redirect('http://localhost/some/redirect/')
    return response(environ, start_response)


def redirect_with_get_app(environ, start_response):
    req = Request(environ)
    if req.url not in ('http://localhost/',
                       'http://localhost/first/request',
                       'http://localhost/some/redirect/'):
        assert False, 'redirect_demo_app() did not expect URL "%s"' % req.url
    if '/some/redirect' not in req.url:
        response = redirect('http://localhost/some/redirect/')
    else:
        response = Response('current url: %s' % req.url)
    return response(environ, start_response)


def redirect_with_post_app(environ, start_response):
    req = Request(environ)
    if req.url == 'http://localhost/some/redirect/':
        assert req.method == 'GET', 'request should be GET'
        assert not req.form, 'request should not have data'
        response = Response('current url: %s' % req.url)
    else:
        response = redirect('http://localhost/some/redirect/')
    return response(environ, start_response)


def external_redirect_demo_app(environ, start_response):
    response = redirect('http://example.com/')
    return response(environ, start_response)


def external_subdomain_redirect_demo_app(environ, start_response):
    if 'test.example.com' in environ['HTTP_HOST']:
        response = Response('redirected successfully to subdomain')
    else:
        response = redirect('http://test.example.com/login')
    return response(environ, start_response)


def multi_value_post_app(environ, start_response):
    req = Request(environ)
    assert req.form['field'] == 'val1', req.form['field']
    assert req.form.getlist('field') == ['val1', 'val2'], req.form.getlist('field')
    response = Response('ok')
    return response(environ, start_response)


class TestTestCase(WerkzeugTestCase):

    def test_cookie_forging(self):
        c = Client(cookie_app)
        c.set_cookie('localhost', 'foo', 'bar')
        appiter, code, headers = c.open()
        self.assert_strict_equal(list(appiter), [b'foo=bar'])

    def test_set_cookie_app(self):
        c = Client(cookie_app)
        appiter, code, headers = c.open()
        self.assert_in('Set-Cookie', dict(headers))

    def test_cookiejar_stores_cookie(self):
        c = Client(cookie_app)
        appiter, code, headers = c.open()
        self.assert_in('test', c.cookie_jar._cookies['localhost.local']['/'])

    def test_no_initial_cookie(self):
        c = Client(cookie_app)
        appiter, code, headers = c.open()
        self.assert_strict_equal(b''.join(appiter), b'No Cookie')

    def test_resent_cookie(self):
        c = Client(cookie_app)
        c.open()
        appiter, code, headers = c.open()
        self.assert_strict_equal(b''.join(appiter), b'test=test')

    def test_disable_cookies(self):
        c = Client(cookie_app, use_cookies=False)
        c.open()
        appiter, code, headers = c.open()
        self.assert_strict_equal(b''.join(appiter), b'No Cookie')

    def test_cookie_for_different_path(self):
        c = Client(cookie_app)
        c.open('/path1')
        appiter, code, headers = c.open('/path2')
        self.assert_strict_equal(b''.join(appiter), b'test=test')

    def test_environ_builder_basics(self):
        b = EnvironBuilder()
        self.assert_is_none(b.content_type)
        b.method = 'POST'
        self.assert_equal(b.content_type, 'application/x-www-form-urlencoded')
        b.files.add_file('test', BytesIO(b'test contents'), 'test.txt')
        self.assert_equal(b.files['test'].content_type, 'text/plain')
        self.assert_equal(b.content_type, 'multipart/form-data')
        b.form['test'] = 'normal value'

        req = b.get_request()
        b.close()

        self.assert_strict_equal(req.url, u'http://localhost/')
        self.assert_strict_equal(req.method, 'POST')
        self.assert_strict_equal(req.form['test'], u'normal value')
        self.assert_equal(req.files['test'].content_type, 'text/plain')
        self.assert_strict_equal(req.files['test'].filename, u'test.txt')
        self.assert_strict_equal(req.files['test'].read(), b'test contents')

    def test_environ_builder_headers(self):
        b = EnvironBuilder(environ_base={'HTTP_USER_AGENT': 'Foo/0.1'},
                           environ_overrides={'wsgi.version': (1, 1)})
        b.headers['X-Suck-My-Dick'] = 'very well sir'
        env = b.get_environ()
        self.assert_strict_equal(env['HTTP_USER_AGENT'], 'Foo/0.1')
        self.assert_strict_equal(env['HTTP_X_SUCK_MY_DICK'], 'very well sir')
        self.assert_strict_equal(env['wsgi.version'], (1, 1))

        b.headers['User-Agent'] = 'Bar/1.0'
        env = b.get_environ()
        self.assert_strict_equal(env['HTTP_USER_AGENT'], 'Bar/1.0')

    def test_environ_builder_headers_content_type(self):
        b = EnvironBuilder(headers={'Content-Type': 'text/plain'})
        env = b.get_environ()
        self.assert_equal(env['CONTENT_TYPE'], 'text/plain')
        b = EnvironBuilder(content_type='text/html',
                           headers={'Content-Type': 'text/plain'})
        env = b.get_environ()
        self.assert_equal(env['CONTENT_TYPE'], 'text/html')

    def test_environ_builder_paths(self):
        b = EnvironBuilder(path='/foo', base_url='http://example.com/')
        self.assert_strict_equal(b.base_url, 'http://example.com/')
        self.assert_strict_equal(b.path, '/foo')
        self.assert_strict_equal(b.script_root, '')
        self.assert_strict_equal(b.host, 'example.com')

        b = EnvironBuilder(path='/foo', base_url='http://example.com/bar')
        self.assert_strict_equal(b.base_url, 'http://example.com/bar/')
        self.assert_strict_equal(b.path, '/foo')
        self.assert_strict_equal(b.script_root, '/bar')
        self.assert_strict_equal(b.host, 'example.com')

        b.host = 'localhost'
        self.assert_strict_equal(b.base_url, 'http://localhost/bar/')
        b.base_url = 'http://localhost:8080/'
        self.assert_strict_equal(b.host, 'localhost:8080')
        self.assert_strict_equal(b.server_name, 'localhost')
        self.assert_strict_equal(b.server_port, 8080)

        b.host = 'foo.invalid'
        b.url_scheme = 'https'
        b.script_root = '/test'
        env = b.get_environ()
        self.assert_strict_equal(env['SERVER_NAME'], 'foo.invalid')
        self.assert_strict_equal(env['SERVER_PORT'], '443')
        self.assert_strict_equal(env['SCRIPT_NAME'], '/test')
        self.assert_strict_equal(env['PATH_INFO'], '/foo')
        self.assert_strict_equal(env['HTTP_HOST'], 'foo.invalid')
        self.assert_strict_equal(env['wsgi.url_scheme'], 'https')
        self.assert_strict_equal(b.base_url, 'https://foo.invalid/test/')

    def test_environ_builder_content_type(self):
        builder = EnvironBuilder()
        self.assert_is_none(builder.content_type)
        builder.method = 'POST'
        self.assert_equal(builder.content_type, 'application/x-www-form-urlencoded')
        builder.form['foo'] = 'bar'
        self.assert_equal(builder.content_type, 'application/x-www-form-urlencoded')
        builder.files.add_file('blafasel', BytesIO(b'foo'), 'test.txt')
        self.assert_equal(builder.content_type, 'multipart/form-data')
        req = builder.get_request()
        self.assert_strict_equal(req.form['foo'], u'bar')
        self.assert_strict_equal(req.files['blafasel'].read(), b'foo')

    def test_environ_builder_stream_switch(self):
        d = MultiDict(dict(foo=u'bar', blub=u'blah', hu=u'hum'))
        for use_tempfile in False, True:
            stream, length, boundary = stream_encode_multipart(
                d, use_tempfile, threshold=150)
            self.assert_true(isinstance(stream, BytesIO) != use_tempfile)

            form = parse_form_data({'wsgi.input': stream, 'CONTENT_LENGTH': str(length),
                                    'CONTENT_TYPE': 'multipart/form-data; boundary="%s"' %
                                    boundary})[1]
            self.assert_strict_equal(form, d)
            stream.close()

    def test_environ_builder_unicode_file_mix(self):
        for use_tempfile in False, True:
            f = FileStorage(BytesIO(u'\N{SNOWMAN}'.encode('utf-8')),
                            'snowman.txt')
            d = MultiDict(dict(f=f, s=u'\N{SNOWMAN}'))
            stream, length, boundary = stream_encode_multipart(
                d, use_tempfile, threshold=150)
            self.assert_true(isinstance(stream, BytesIO) != use_tempfile)

            _, form, files = parse_form_data({
                'wsgi.input': stream,
                'CONTENT_LENGTH': str(length),
                'CONTENT_TYPE': 'multipart/form-data; boundary="%s"' %
                                    boundary
            })
            self.assert_strict_equal(form['s'], u'\N{SNOWMAN}')
            self.assert_strict_equal(files['f'].name, 'f')
            self.assert_strict_equal(files['f'].filename, u'snowman.txt')
            self.assert_strict_equal(files['f'].read(),
                                     u'\N{SNOWMAN}'.encode('utf-8'))
            stream.close()

    def test_create_environ(self):
        env = create_environ('/foo?bar=baz', 'http://example.org/')
        expected = {
            'wsgi.multiprocess':    False,
            'wsgi.version':         (1, 0),
            'wsgi.run_once':        False,
            'wsgi.errors':          sys.stderr,
            'wsgi.multithread':     False,
            'wsgi.url_scheme':      'http',
            'SCRIPT_NAME':          '',
            'CONTENT_TYPE':         '',
            'CONTENT_LENGTH':       '0',
            'SERVER_NAME':          'example.org',
            'REQUEST_METHOD':       'GET',
            'HTTP_HOST':            'example.org',
            'PATH_INFO':            '/foo',
            'SERVER_PORT':          '80',
            'SERVER_PROTOCOL':      'HTTP/1.1',
            'QUERY_STRING':         'bar=baz'
        }
        for key, value in iteritems(expected):
            self.assert_equal(env[key], value)
        self.assert_strict_equal(env['wsgi.input'].read(0), b'')
        self.assert_strict_equal(create_environ('/foo', 'http://example.com/')['SCRIPT_NAME'], '')

    def test_file_closing(self):
        closed = []
        class SpecialInput(object):
            def read(self):
                return ''
            def close(self):
                closed.append(self)

        env = create_environ(data={'foo': SpecialInput()})
        self.assert_strict_equal(len(closed), 1)
        builder = EnvironBuilder()
        builder.files.add_file('blah', SpecialInput())
        builder.close()
        self.assert_strict_equal(len(closed), 2)

    def test_follow_redirect(self):
        env = create_environ('/', base_url='http://localhost')
        c = Client(redirect_with_get_app)
        appiter, code, headers = c.open(environ_overrides=env, follow_redirects=True)
        self.assert_strict_equal(code, '200 OK')
        self.assert_strict_equal(b''.join(appiter), b'current url: http://localhost/some/redirect/')

        # Test that the :cls:`Client` is aware of user defined response wrappers
        c = Client(redirect_with_get_app, response_wrapper=BaseResponse)
        resp = c.get('/', follow_redirects=True)
        self.assert_strict_equal(resp.status_code, 200)
        self.assert_strict_equal(resp.data, b'current url: http://localhost/some/redirect/')

        # test with URL other than '/' to make sure redirected URL's are correct
        c = Client(redirect_with_get_app, response_wrapper=BaseResponse)
        resp = c.get('/first/request', follow_redirects=True)
        self.assert_strict_equal(resp.status_code, 200)
        self.assert_strict_equal(resp.data, b'current url: http://localhost/some/redirect/')

    def test_follow_external_redirect(self):
        env = create_environ('/', base_url='http://localhost')
        c = Client(external_redirect_demo_app)
        self.assert_raises(RuntimeError, lambda:
            c.get(environ_overrides=env, follow_redirects=True))

    def test_follow_external_redirect_on_same_subdomain(self):
        env = create_environ('/', base_url='http://example.com')
        c = Client(external_subdomain_redirect_demo_app, allow_subdomain_redirects=True)
        c.get(environ_overrides=env, follow_redirects=True)

        # check that this does not work for real external domains
        env = create_environ('/', base_url='http://localhost')
        self.assert_raises(RuntimeError, lambda:
            c.get(environ_overrides=env, follow_redirects=True))

        # check that subdomain redirects fail if no `allow_subdomain_redirects` is applied
        c = Client(external_subdomain_redirect_demo_app)
        self.assert_raises(RuntimeError, lambda:
            c.get(environ_overrides=env, follow_redirects=True))

    def test_follow_redirect_loop(self):
        c = Client(redirect_loop_app, response_wrapper=BaseResponse)
        with self.assert_raises(ClientRedirectError):
            resp = c.get('/', follow_redirects=True)

    def test_follow_redirect_with_post(self):
        c = Client(redirect_with_post_app, response_wrapper=BaseResponse)
        resp = c.post('/', follow_redirects=True, data='foo=blub+hehe&blah=42')
        self.assert_strict_equal(resp.status_code, 200)
        self.assert_strict_equal(resp.data, b'current url: http://localhost/some/redirect/')

    def test_path_info_script_name_unquoting(self):
        def test_app(environ, start_response):
            start_response('200 OK', [('Content-Type', 'text/plain')])
            return [environ['PATH_INFO'] + '\n' + environ['SCRIPT_NAME']]
        c = Client(test_app, response_wrapper=BaseResponse)
        resp = c.get('/foo%40bar')
        self.assert_strict_equal(resp.data, b'/foo@bar\n')
        c = Client(test_app, response_wrapper=BaseResponse)
        resp = c.get('/foo%40bar', 'http://localhost/bar%40baz')
        self.assert_strict_equal(resp.data, b'/foo@bar\n/bar@baz')

    def test_multi_value_submit(self):
        c = Client(multi_value_post_app, response_wrapper=BaseResponse)
        data = {
            'field': ['val1','val2']
        }
        resp = c.post('/', data=data)
        self.assert_strict_equal(resp.status_code, 200)
        c = Client(multi_value_post_app, response_wrapper=BaseResponse)
        data = MultiDict({
            'field': ['val1', 'val2']
        })
        resp = c.post('/', data=data)
        self.assert_strict_equal(resp.status_code, 200)

    def test_iri_support(self):
        b = EnvironBuilder(u'/föö-bar', base_url=u'http://☃.net/')
        self.assert_strict_equal(b.path, '/f%C3%B6%C3%B6-bar')
        self.assert_strict_equal(b.base_url, 'http://xn--n3h.net/')

    def test_run_wsgi_apps(self):
        def simple_app(environ, start_response):
            start_response('200 OK', [('Content-Type', 'text/html')])
            return ['Hello World!']
        app_iter, status, headers = run_wsgi_app(simple_app, {})
        self.assert_strict_equal(status, '200 OK')
        self.assert_strict_equal(list(headers), [('Content-Type', 'text/html')])
        self.assert_strict_equal(app_iter, ['Hello World!'])

        def yielding_app(environ, start_response):
            start_response('200 OK', [('Content-Type', 'text/html')])
            yield 'Hello '
            yield 'World!'
        app_iter, status, headers = run_wsgi_app(yielding_app, {})
        self.assert_strict_equal(status, '200 OK')
        self.assert_strict_equal(list(headers), [('Content-Type', 'text/html')])
        self.assert_strict_equal(list(app_iter), ['Hello ', 'World!'])

    def test_multiple_cookies(self):
        @Request.application
        def test_app(request):
            response = Response(repr(sorted(request.cookies.items())))
            response.set_cookie(u'test1', b'foo')
            response.set_cookie(u'test2', b'bar')
            return response
        client = Client(test_app, Response)
        resp = client.get('/')
        self.assert_strict_equal(resp.data, b'[]')
        resp = client.get('/')
        self.assert_strict_equal(resp.data,
                          to_bytes(repr([('test1', u'foo'), ('test2', u'bar')]), 'ascii'))

    def test_correct_open_invocation_on_redirect(self):
        class MyClient(Client):
            counter = 0
            def open(self, *args, **kwargs):
                self.counter += 1
                env = kwargs.setdefault('environ_overrides', {})
                env['werkzeug._foo'] = self.counter
                return Client.open(self, *args, **kwargs)

        @Request.application
        def test_app(request):
            return Response(str(request.environ['werkzeug._foo']))

        c = MyClient(test_app, response_wrapper=Response)
        self.assert_strict_equal(c.get('/').data, b'1')
        self.assert_strict_equal(c.get('/').data, b'2')
        self.assert_strict_equal(c.get('/').data, b'3')

    def test_correct_encoding(self):
        req = Request.from_values(u'/\N{SNOWMAN}', u'http://example.com/foo')
        self.assert_strict_equal(req.script_root, u'/foo')
        self.assert_strict_equal(req.path, u'/\N{SNOWMAN}')

    def test_full_url_requests_with_args(self):
        base = 'http://example.com/'

        @Request.application
        def test_app(request):
            return Response(request.args['x'])
        client = Client(test_app, Response)
        resp = client.get('/?x=42', base)
        self.assert_strict_equal(resp.data, b'42')
        resp = client.get('http://www.example.com/?x=23', base)
        self.assert_strict_equal(resp.data, b'23')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestTestCase))
    return suite
