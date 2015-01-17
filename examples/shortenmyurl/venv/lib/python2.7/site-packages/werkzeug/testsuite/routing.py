# -*- coding: utf-8 -*-
"""
    werkzeug.testsuite.routing
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Routing tests.

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import unittest

from werkzeug.testsuite import WerkzeugTestCase

from werkzeug import routing as r
from werkzeug.wrappers import Response
from werkzeug.datastructures import ImmutableDict
from werkzeug.test import create_environ


class RoutingTestCase(WerkzeugTestCase):

    def test_basic_routing(self):
        map = r.Map([
            r.Rule('/', endpoint='index'),
            r.Rule('/foo', endpoint='foo'),
            r.Rule('/bar/', endpoint='bar')
        ])
        adapter = map.bind('example.org', '/')
        assert adapter.match('/') == ('index', {})
        assert adapter.match('/foo') == ('foo', {})
        assert adapter.match('/bar/') == ('bar', {})
        self.assert_raises(r.RequestRedirect, lambda: adapter.match('/bar'))
        self.assert_raises(r.NotFound, lambda: adapter.match('/blub'))

        adapter = map.bind('example.org', '/test')
        try:
            adapter.match('/bar')
        except r.RequestRedirect as e:
            assert e.new_url == 'http://example.org/test/bar/'
        else:
            self.fail('Expected request redirect')

        adapter = map.bind('example.org', '/')
        try:
            adapter.match('/bar')
        except r.RequestRedirect as e:
            assert e.new_url == 'http://example.org/bar/'
        else:
            self.fail('Expected request redirect')

        adapter = map.bind('example.org', '/')
        try:
            adapter.match('/bar', query_args={'aha': 'muhaha'})
        except r.RequestRedirect as e:
            assert e.new_url == 'http://example.org/bar/?aha=muhaha'
        else:
            self.fail('Expected request redirect')

        adapter = map.bind('example.org', '/')
        try:
            adapter.match('/bar', query_args='aha=muhaha')
        except r.RequestRedirect as e:
            assert e.new_url == 'http://example.org/bar/?aha=muhaha'
        else:
            self.fail('Expected request redirect')

        adapter = map.bind_to_environ(create_environ('/bar?foo=bar',
                                                     'http://example.org/'))
        try:
            adapter.match()
        except r.RequestRedirect as e:
            assert e.new_url == 'http://example.org/bar/?foo=bar'
        else:
            self.fail('Expected request redirect')

    def test_environ_defaults(self):
        environ = create_environ("/foo")
        self.assert_strict_equal(environ["PATH_INFO"], '/foo')
        m = r.Map([r.Rule("/foo", endpoint="foo"), r.Rule("/bar", endpoint="bar")])
        a = m.bind_to_environ(environ)
        self.assert_strict_equal(a.match("/foo"), ('foo', {}))
        self.assert_strict_equal(a.match(), ('foo', {}))
        self.assert_strict_equal(a.match("/bar"), ('bar', {}))
        self.assert_raises(r.NotFound, a.match, "/bars")

    def test_environ_nonascii_pathinfo(self):
        environ = create_environ(u'/лошадь')
        m = r.Map([
            r.Rule(u'/', endpoint='index'),
            r.Rule(u'/лошадь', endpoint='horse')
        ])
        a = m.bind_to_environ(environ)
        self.assert_strict_equal(a.match(u'/'), ('index', {}))
        self.assert_strict_equal(a.match(u'/лошадь'), ('horse', {}))
        self.assert_raises(r.NotFound, a.match, u'/барсук')

    def test_basic_building(self):
        map = r.Map([
            r.Rule('/', endpoint='index'),
            r.Rule('/foo', endpoint='foo'),
            r.Rule('/bar/<baz>', endpoint='bar'),
            r.Rule('/bar/<int:bazi>', endpoint='bari'),
            r.Rule('/bar/<float:bazf>', endpoint='barf'),
            r.Rule('/bar/<path:bazp>', endpoint='barp'),
            r.Rule('/hehe', endpoint='blah', subdomain='blah')
        ])
        adapter = map.bind('example.org', '/', subdomain='blah')

        assert adapter.build('index', {}) == 'http://example.org/'
        assert adapter.build('foo', {}) == 'http://example.org/foo'
        assert adapter.build('bar', {'baz': 'blub'}) == 'http://example.org/bar/blub'
        assert adapter.build('bari', {'bazi': 50}) == 'http://example.org/bar/50'
        assert adapter.build('barf', {'bazf': 0.815}) == 'http://example.org/bar/0.815'
        assert adapter.build('barp', {'bazp': 'la/di'}) == 'http://example.org/bar/la/di'
        assert adapter.build('blah', {}) == '/hehe'
        self.assert_raises(r.BuildError, lambda: adapter.build('urks'))

        adapter = map.bind('example.org', '/test', subdomain='blah')
        assert adapter.build('index', {}) == 'http://example.org/test/'
        assert adapter.build('foo', {}) == 'http://example.org/test/foo'
        assert adapter.build('bar', {'baz': 'blub'}) == 'http://example.org/test/bar/blub'
        assert adapter.build('bari', {'bazi': 50}) == 'http://example.org/test/bar/50'
        assert adapter.build('barf', {'bazf': 0.815}) == 'http://example.org/test/bar/0.815'
        assert adapter.build('barp', {'bazp': 'la/di'}) == 'http://example.org/test/bar/la/di'
        assert adapter.build('blah', {}) == '/test/hehe'

    def test_defaults(self):
        map = r.Map([
            r.Rule('/foo/', defaults={'page': 1}, endpoint='foo'),
            r.Rule('/foo/<int:page>', endpoint='foo')
        ])
        adapter = map.bind('example.org', '/')

        assert adapter.match('/foo/') == ('foo', {'page': 1})
        self.assert_raises(r.RequestRedirect, lambda: adapter.match('/foo/1'))
        assert adapter.match('/foo/2') == ('foo', {'page': 2})
        assert adapter.build('foo', {}) == '/foo/'
        assert adapter.build('foo', {'page': 1}) == '/foo/'
        assert adapter.build('foo', {'page': 2}) == '/foo/2'

    def test_greedy(self):
        map = r.Map([
            r.Rule('/foo', endpoint='foo'),
            r.Rule('/<path:bar>', endpoint='bar'),
            r.Rule('/<path:bar>/<path:blub>', endpoint='bar')
        ])
        adapter = map.bind('example.org', '/')

        assert adapter.match('/foo') == ('foo', {})
        assert adapter.match('/blub') == ('bar', {'bar': 'blub'})
        assert adapter.match('/he/he') == ('bar', {'bar': 'he', 'blub': 'he'})

        assert adapter.build('foo', {}) == '/foo'
        assert adapter.build('bar', {'bar': 'blub'}) == '/blub'
        assert adapter.build('bar', {'bar': 'blub', 'blub': 'bar'}) == '/blub/bar'

    def test_path(self):
        map = r.Map([
            r.Rule('/', defaults={'name': 'FrontPage'}, endpoint='page'),
            r.Rule('/Special', endpoint='special'),
            r.Rule('/<int:year>', endpoint='year'),
            r.Rule('/<path:name>', endpoint='page'),
            r.Rule('/<path:name>/edit', endpoint='editpage'),
            r.Rule('/<path:name>/silly/<path:name2>', endpoint='sillypage'),
            r.Rule('/<path:name>/silly/<path:name2>/edit', endpoint='editsillypage'),
            r.Rule('/Talk:<path:name>', endpoint='talk'),
            r.Rule('/User:<username>', endpoint='user'),
            r.Rule('/User:<username>/<path:name>', endpoint='userpage'),
            r.Rule('/Files/<path:file>', endpoint='files'),
        ])
        adapter = map.bind('example.org', '/')

        assert adapter.match('/') == ('page', {'name':'FrontPage'})
        self.assert_raises(r.RequestRedirect, lambda: adapter.match('/FrontPage'))
        assert adapter.match('/Special') == ('special', {})
        assert adapter.match('/2007') == ('year', {'year':2007})
        assert adapter.match('/Some/Page') == ('page', {'name':'Some/Page'})
        assert adapter.match('/Some/Page/edit') == ('editpage', {'name':'Some/Page'})
        assert adapter.match('/Foo/silly/bar') == ('sillypage', {'name':'Foo', 'name2':'bar'})
        assert adapter.match('/Foo/silly/bar/edit') == ('editsillypage', {'name':'Foo', 'name2':'bar'})
        assert adapter.match('/Talk:Foo/Bar') == ('talk', {'name':'Foo/Bar'})
        assert adapter.match('/User:thomas') == ('user', {'username':'thomas'})
        assert adapter.match('/User:thomas/projects/werkzeug') == \
            ('userpage', {'username':'thomas', 'name':'projects/werkzeug'})
        assert adapter.match('/Files/downloads/werkzeug/0.2.zip') == \
            ('files', {'file':'downloads/werkzeug/0.2.zip'})

    def test_dispatch(self):
        env = create_environ('/')
        map = r.Map([
            r.Rule('/', endpoint='root'),
            r.Rule('/foo/', endpoint='foo')
        ])
        adapter = map.bind_to_environ(env)

        raise_this = None
        def view_func(endpoint, values):
            if raise_this is not None:
                raise raise_this
            return Response(repr((endpoint, values)))
        dispatch = lambda p, q=False: Response.force_type(adapter.dispatch(view_func, p,
                                                          catch_http_exceptions=q), env)

        assert dispatch('/').data == b"('root', {})"
        assert dispatch('/foo').status_code == 301
        raise_this = r.NotFound()
        self.assert_raises(r.NotFound, lambda: dispatch('/bar'))
        assert dispatch('/bar', True).status_code == 404

    def test_http_host_before_server_name(self):
        env = {
            'HTTP_HOST':            'wiki.example.com',
            'SERVER_NAME':          'web0.example.com',
            'SERVER_PORT':          '80',
            'SCRIPT_NAME':          '',
            'PATH_INFO':            '',
            'REQUEST_METHOD':       'GET',
            'wsgi.url_scheme':      'http'
        }
        map = r.Map([r.Rule('/', endpoint='index', subdomain='wiki')])
        adapter = map.bind_to_environ(env, server_name='example.com')
        assert adapter.match('/') == ('index', {})
        assert adapter.build('index', force_external=True) == 'http://wiki.example.com/'
        assert adapter.build('index') == '/'

        env['HTTP_HOST'] = 'admin.example.com'
        adapter = map.bind_to_environ(env, server_name='example.com')
        assert adapter.build('index') == 'http://wiki.example.com/'

    def test_adapter_url_parameter_sorting(self):
        map = r.Map([r.Rule('/', endpoint='index')], sort_parameters=True,
                     sort_key=lambda x: x[1])
        adapter = map.bind('localhost', '/')
        assert adapter.build('index', {'x': 20, 'y': 10, 'z': 30},
            force_external=True) == 'http://localhost/?y=10&x=20&z=30'

    def test_request_direct_charset_bug(self):
        map = r.Map([r.Rule(u'/öäü/')])
        adapter = map.bind('localhost', '/')
        try:
            adapter.match(u'/öäü')
        except r.RequestRedirect as e:
            assert e.new_url == 'http://localhost/%C3%B6%C3%A4%C3%BC/'
        else:
            self.fail('expected request redirect exception')

    def test_request_redirect_default(self):
        map = r.Map([r.Rule(u'/foo', defaults={'bar': 42}),
                     r.Rule(u'/foo/<int:bar>')])
        adapter = map.bind('localhost', '/')
        try:
            adapter.match(u'/foo/42')
        except r.RequestRedirect as e:
            assert e.new_url == 'http://localhost/foo'
        else:
            self.fail('expected request redirect exception')

    def test_request_redirect_default_subdomain(self):
        map = r.Map([r.Rule(u'/foo', defaults={'bar': 42}, subdomain='test'),
                     r.Rule(u'/foo/<int:bar>', subdomain='other')])
        adapter = map.bind('localhost', '/', subdomain='other')
        try:
            adapter.match(u'/foo/42')
        except r.RequestRedirect as e:
            assert e.new_url == 'http://test.localhost/foo'
        else:
            self.fail('expected request redirect exception')

    def test_adapter_match_return_rule(self):
        rule = r.Rule('/foo/', endpoint='foo')
        map = r.Map([rule])
        adapter = map.bind('localhost', '/')
        assert adapter.match('/foo/', return_rule=True) == (rule, {})

    def test_server_name_interpolation(self):
        server_name = 'example.invalid'
        map = r.Map([r.Rule('/', endpoint='index'),
                     r.Rule('/', endpoint='alt', subdomain='alt')])

        env = create_environ('/', 'http://%s/' % server_name)
        adapter = map.bind_to_environ(env, server_name=server_name)
        assert adapter.match() == ('index', {})

        env = create_environ('/', 'http://alt.%s/' % server_name)
        adapter = map.bind_to_environ(env, server_name=server_name)
        assert adapter.match() == ('alt', {})

        env = create_environ('/', 'http://%s/' % server_name)
        adapter = map.bind_to_environ(env, server_name='foo')
        assert adapter.subdomain == '<invalid>'

    def test_rule_emptying(self):
        rule = r.Rule('/foo', {'meh': 'muh'}, 'x', ['POST'],
                   False, 'x', True, None)
        rule2 = rule.empty()
        assert rule.__dict__ == rule2.__dict__
        rule.methods.add('GET')
        assert rule.__dict__ != rule2.__dict__
        rule.methods.discard('GET')
        rule.defaults['meh'] = 'aha'
        assert rule.__dict__ != rule2.__dict__

    def test_rule_templates(self):
        testcase = r.RuleTemplate(
            [ r.Submount('/test/$app',
              [ r.Rule('/foo/', endpoint='handle_foo')
              , r.Rule('/bar/', endpoint='handle_bar')
              , r.Rule('/baz/', endpoint='handle_baz')
              ]),
              r.EndpointPrefix('${app}',
              [ r.Rule('/${app}-blah', endpoint='bar')
              , r.Rule('/${app}-meh', endpoint='baz')
              ]),
              r.Subdomain('$app',
              [ r.Rule('/blah', endpoint='x_bar')
              , r.Rule('/meh', endpoint='x_baz')
              ])
            ])

        url_map = r.Map(
            [ testcase(app='test1')
            , testcase(app='test2')
            , testcase(app='test3')
            , testcase(app='test4')
            ])

        out = sorted([(x.rule, x.subdomain, x.endpoint)
                      for x in url_map.iter_rules()])

        assert out == ([
            ('/blah', 'test1', 'x_bar'),
            ('/blah', 'test2', 'x_bar'),
            ('/blah', 'test3', 'x_bar'),
            ('/blah', 'test4', 'x_bar'),
            ('/meh', 'test1', 'x_baz'),
            ('/meh', 'test2', 'x_baz'),
            ('/meh', 'test3', 'x_baz'),
            ('/meh', 'test4', 'x_baz'),
            ('/test/test1/bar/', '', 'handle_bar'),
            ('/test/test1/baz/', '', 'handle_baz'),
            ('/test/test1/foo/', '', 'handle_foo'),
            ('/test/test2/bar/', '', 'handle_bar'),
            ('/test/test2/baz/', '', 'handle_baz'),
            ('/test/test2/foo/', '', 'handle_foo'),
            ('/test/test3/bar/', '', 'handle_bar'),
            ('/test/test3/baz/', '', 'handle_baz'),
            ('/test/test3/foo/', '', 'handle_foo'),
            ('/test/test4/bar/', '', 'handle_bar'),
            ('/test/test4/baz/', '', 'handle_baz'),
            ('/test/test4/foo/', '', 'handle_foo'),
            ('/test1-blah', '', 'test1bar'),
            ('/test1-meh', '', 'test1baz'),
            ('/test2-blah', '', 'test2bar'),
            ('/test2-meh', '', 'test2baz'),
            ('/test3-blah', '', 'test3bar'),
            ('/test3-meh', '', 'test3baz'),
            ('/test4-blah', '', 'test4bar'),
            ('/test4-meh', '', 'test4baz')
        ])

    def test_non_string_parts(self):
        m = r.Map([
            r.Rule('/<foo>', endpoint='foo')
        ])
        a = m.bind('example.com')
        self.assert_equal(a.build('foo', {'foo': 42}), '/42')

    def test_complex_routing_rules(self):
        m = r.Map([
            r.Rule('/', endpoint='index'),
            r.Rule('/<int:blub>', endpoint='an_int'),
            r.Rule('/<blub>', endpoint='a_string'),
            r.Rule('/foo/', endpoint='nested'),
            r.Rule('/foobar/', endpoint='nestedbar'),
            r.Rule('/foo/<path:testing>/', endpoint='nested_show'),
            r.Rule('/foo/<path:testing>/edit', endpoint='nested_edit'),
            r.Rule('/users/', endpoint='users', defaults={'page': 1}),
            r.Rule('/users/page/<int:page>', endpoint='users'),
            r.Rule('/foox', endpoint='foox'),
            r.Rule('/<path:bar>/<path:blub>', endpoint='barx_path_path')
        ])
        a = m.bind('example.com')

        assert a.match('/') == ('index', {})
        assert a.match('/42') == ('an_int', {'blub': 42})
        assert a.match('/blub') == ('a_string', {'blub': 'blub'})
        assert a.match('/foo/') == ('nested', {})
        assert a.match('/foobar/') == ('nestedbar', {})
        assert a.match('/foo/1/2/3/') == ('nested_show', {'testing': '1/2/3'})
        assert a.match('/foo/1/2/3/edit') == ('nested_edit', {'testing': '1/2/3'})
        assert a.match('/users/') == ('users', {'page': 1})
        assert a.match('/users/page/2') == ('users', {'page': 2})
        assert a.match('/foox') == ('foox', {})
        assert a.match('/1/2/3') == ('barx_path_path', {'bar': '1', 'blub': '2/3'})

        assert a.build('index') == '/'
        assert a.build('an_int', {'blub': 42}) == '/42'
        assert a.build('a_string', {'blub': 'test'}) == '/test'
        assert a.build('nested') == '/foo/'
        assert a.build('nestedbar') == '/foobar/'
        assert a.build('nested_show', {'testing': '1/2/3'}) == '/foo/1/2/3/'
        assert a.build('nested_edit', {'testing': '1/2/3'}) == '/foo/1/2/3/edit'
        assert a.build('users', {'page': 1}) == '/users/'
        assert a.build('users', {'page': 2}) == '/users/page/2'
        assert a.build('foox') == '/foox'
        assert a.build('barx_path_path', {'bar': '1', 'blub': '2/3'}) == '/1/2/3'

    def test_default_converters(self):
        class MyMap(r.Map):
            default_converters = r.Map.default_converters.copy()
            default_converters['foo'] = r.UnicodeConverter
        assert isinstance(r.Map.default_converters, ImmutableDict)
        m = MyMap([
            r.Rule('/a/<foo:a>', endpoint='a'),
            r.Rule('/b/<foo:b>', endpoint='b'),
            r.Rule('/c/<c>', endpoint='c')
        ], converters={'bar': r.UnicodeConverter})
        a = m.bind('example.org', '/')
        assert a.match('/a/1') == ('a', {'a': '1'})
        assert a.match('/b/2') == ('b', {'b': '2'})
        assert a.match('/c/3') == ('c', {'c': '3'})
        assert 'foo' not in r.Map.default_converters

    def test_build_append_unknown(self):
        map = r.Map([
            r.Rule('/bar/<float:bazf>', endpoint='barf')
        ])
        adapter = map.bind('example.org', '/', subdomain='blah')
        assert adapter.build('barf', {'bazf': 0.815, 'bif' : 1.0}) == \
            'http://example.org/bar/0.815?bif=1.0'
        assert adapter.build('barf', {'bazf': 0.815, 'bif' : 1.0},
            append_unknown=False) == 'http://example.org/bar/0.815'

    def test_method_fallback(self):
        map = r.Map([
            r.Rule('/', endpoint='index', methods=['GET']),
            r.Rule('/<name>', endpoint='hello_name', methods=['GET']),
            r.Rule('/select', endpoint='hello_select', methods=['POST']),
            r.Rule('/search_get', endpoint='search', methods=['GET']),
            r.Rule('/search_post', endpoint='search', methods=['POST'])
        ])
        adapter = map.bind('example.com')
        assert adapter.build('index') == '/'
        assert adapter.build('index', method='GET') == '/'
        assert adapter.build('hello_name', {'name': 'foo'}) == '/foo'
        assert adapter.build('hello_select') == '/select'
        assert adapter.build('hello_select', method='POST') == '/select'
        assert adapter.build('search') == '/search_get'
        assert adapter.build('search', method='GET') == '/search_get'
        assert adapter.build('search', method='POST') == '/search_post'

    def test_implicit_head(self):
        url_map = r.Map([
            r.Rule('/get', methods=['GET'], endpoint='a'),
            r.Rule('/post', methods=['POST'], endpoint='b')
        ])
        adapter = url_map.bind('example.org')
        assert adapter.match('/get', method='HEAD') == ('a', {})
        self.assert_raises(r.MethodNotAllowed, adapter.match,
                           '/post', method='HEAD')

    def test_protocol_joining_bug(self):
        m = r.Map([r.Rule('/<foo>', endpoint='x')])
        a = m.bind('example.org')
        assert a.build('x', {'foo': 'x:y'}) == '/x:y'
        assert a.build('x', {'foo': 'x:y'}, force_external=True) == \
            'http://example.org/x:y'

    def test_allowed_methods_querying(self):
        m = r.Map([r.Rule('/<foo>', methods=['GET', 'HEAD']),
                   r.Rule('/foo', methods=['POST'])])
        a = m.bind('example.org')
        assert sorted(a.allowed_methods('/foo')) == ['GET', 'HEAD', 'POST']

    def test_external_building_with_port(self):
        map = r.Map([
            r.Rule('/', endpoint='index'),
        ])
        adapter = map.bind('example.org:5000', '/')
        built_url = adapter.build('index', {}, force_external=True)
        assert built_url == 'http://example.org:5000/', built_url

    def test_external_building_with_port_bind_to_environ(self):
        map = r.Map([
            r.Rule('/', endpoint='index'),
        ])
        adapter = map.bind_to_environ(
            create_environ('/', 'http://example.org:5000/'),
            server_name="example.org:5000"
        )
        built_url = adapter.build('index', {}, force_external=True)
        assert built_url == 'http://example.org:5000/', built_url

    def test_external_building_with_port_bind_to_environ_wrong_servername(self):
        map = r.Map([
            r.Rule('/', endpoint='index'),
        ])
        environ = create_environ('/', 'http://example.org:5000/')
        adapter = map.bind_to_environ(environ, server_name="example.org")
        assert adapter.subdomain == '<invalid>'

    def test_converter_parser(self):
        args, kwargs = r.parse_converter_args(u'test, a=1, b=3.0')

        assert args == ('test',)
        assert kwargs == {'a': 1, 'b': 3.0 }

        args, kwargs = r.parse_converter_args('')
        assert not args and not kwargs

        args, kwargs = r.parse_converter_args('a, b, c,')
        assert args == ('a', 'b', 'c')
        assert not kwargs

        args, kwargs = r.parse_converter_args('True, False, None')
        assert args == (True, False, None)

        args, kwargs = r.parse_converter_args('"foo", u"bar"')
        assert args == ('foo', 'bar')

    def test_alias_redirects(self):
        m = r.Map([
            r.Rule('/', endpoint='index'),
            r.Rule('/index.html', endpoint='index', alias=True),
            r.Rule('/users/', defaults={'page': 1}, endpoint='users'),
            r.Rule('/users/index.html', defaults={'page': 1}, alias=True,
                   endpoint='users'),
            r.Rule('/users/page/<int:page>', endpoint='users'),
            r.Rule('/users/page-<int:page>.html', alias=True, endpoint='users'),
        ])
        a = m.bind('example.com')

        def ensure_redirect(path, new_url, args=None):
            try:
                a.match(path, query_args=args)
            except r.RequestRedirect as e:
                assert e.new_url == 'http://example.com' + new_url
            else:
                assert False, 'expected redirect'

        ensure_redirect('/index.html', '/')
        ensure_redirect('/users/index.html', '/users/')
        ensure_redirect('/users/page-2.html', '/users/page/2')
        ensure_redirect('/users/page-1.html', '/users/')
        ensure_redirect('/users/page-1.html', '/users/?foo=bar', {'foo': 'bar'})

        assert a.build('index') == '/'
        assert a.build('users', {'page': 1}) == '/users/'
        assert a.build('users', {'page': 2}) == '/users/page/2'

    def test_double_defaults(self):
        for prefix in '', '/aaa':
            m = r.Map([
                r.Rule(prefix + '/', defaults={'foo': 1, 'bar': False}, endpoint='x'),
                r.Rule(prefix + '/<int:foo>', defaults={'bar': False}, endpoint='x'),
                r.Rule(prefix + '/bar/', defaults={'foo': 1, 'bar': True}, endpoint='x'),
                r.Rule(prefix + '/bar/<int:foo>', defaults={'bar': True}, endpoint='x')
            ])
            a = m.bind('example.com')

            assert a.match(prefix + '/') == ('x', {'foo': 1, 'bar': False})
            assert a.match(prefix + '/2') == ('x', {'foo': 2, 'bar': False})
            assert a.match(prefix + '/bar/') == ('x', {'foo': 1, 'bar': True})
            assert a.match(prefix + '/bar/2') == ('x', {'foo': 2, 'bar': True})

            assert a.build('x', {'foo': 1, 'bar': False}) == prefix + '/'
            assert a.build('x', {'foo': 2, 'bar': False}) == prefix + '/2'
            assert a.build('x', {'bar': False}) == prefix + '/'
            assert a.build('x', {'foo': 1, 'bar': True}) == prefix + '/bar/'
            assert a.build('x', {'foo': 2, 'bar': True}) == prefix + '/bar/2'
            assert a.build('x', {'bar': True}) == prefix + '/bar/'

    def test_host_matching(self):
        m = r.Map([
            r.Rule('/', endpoint='index', host='www.<domain>'),
            r.Rule('/', endpoint='files', host='files.<domain>'),
            r.Rule('/foo/', defaults={'page': 1}, host='www.<domain>', endpoint='x'),
            r.Rule('/<int:page>', host='files.<domain>', endpoint='x')
        ], host_matching=True)

        a = m.bind('www.example.com')
        assert a.match('/') == ('index', {'domain': 'example.com'})
        assert a.match('/foo/') == ('x', {'domain': 'example.com', 'page': 1})
        try:
            a.match('/foo')
        except r.RequestRedirect as e:
            assert e.new_url == 'http://www.example.com/foo/'
        else:
            assert False, 'expected redirect'

        a = m.bind('files.example.com')
        assert a.match('/') == ('files', {'domain': 'example.com'})
        assert a.match('/2') == ('x', {'domain': 'example.com', 'page': 2})
        try:
            a.match('/1')
        except r.RequestRedirect as e:
            assert e.new_url == 'http://www.example.com/foo/'
        else:
            assert False, 'expected redirect'

    def test_server_name_casing(self):
        m = r.Map([
            r.Rule('/', endpoint='index', subdomain='foo')
        ])

        env = create_environ()
        env['SERVER_NAME'] = env['HTTP_HOST'] = 'FOO.EXAMPLE.COM'
        a = m.bind_to_environ(env, server_name='example.com')
        assert a.match('/') == ('index', {})

        env = create_environ()
        env['SERVER_NAME'] = '127.0.0.1'
        env['SERVER_PORT'] = '5000'
        del env['HTTP_HOST']
        a = m.bind_to_environ(env, server_name='example.com')
        try:
            a.match()
        except r.NotFound:
            pass
        else:
            assert False, 'Expected not found exception'

    def test_redirect_request_exception_code(self):
        exc = r.RequestRedirect('http://www.google.com/')
        exc.code = 307
        env = create_environ()
        self.assert_strict_equal(exc.get_response(env).status_code, exc.code)

    def test_redirect_path_quoting(self):
        url_map = r.Map([
            r.Rule('/<category>', defaults={'page': 1}, endpoint='category'),
            r.Rule('/<category>/page/<int:page>', endpoint='category')
        ])

        adapter = url_map.bind('example.com')
        try:
            adapter.match('/foo bar/page/1')
        except r.RequestRedirect as e:
            response = e.get_response({})
            self.assert_strict_equal(response.headers['location'],
                                     u'http://example.com/foo%20bar')
        else:
            self.fail('Expected redirect')

    def test_unicode_rules(self):
        m = r.Map([
            r.Rule(u'/войти/', endpoint='enter'),
            r.Rule(u'/foo+bar/', endpoint='foobar')
        ])
        a = m.bind(u'☃.example.com')
        try:
            a.match(u'/войти')
        except r.RequestRedirect as e:
            self.assert_strict_equal(e.new_url, 'http://xn--n3h.example.com/'
                              '%D0%B2%D0%BE%D0%B9%D1%82%D0%B8/')
        endpoint, values = a.match(u'/войти/')
        self.assert_strict_equal(endpoint, 'enter')
        self.assert_strict_equal(values, {})

        try:
            a.match(u'/foo+bar')
        except r.RequestRedirect as e:
            self.assert_strict_equal(e.new_url, 'http://xn--n3h.example.com/'
                              'foo+bar/')
        endpoint, values = a.match(u'/foo+bar/')
        self.assert_strict_equal(endpoint, 'foobar')
        self.assert_strict_equal(values, {})

        url = a.build('enter', {}, force_external=True)
        self.assert_strict_equal(url, 'http://xn--n3h.example.com/%D0%B2%D0%BE%D0%B9%D1%82%D0%B8/')

        url = a.build('foobar', {}, force_external=True)
        self.assert_strict_equal(url, 'http://xn--n3h.example.com/foo+bar/')

    def test_map_repr(self):
        m = r.Map([
            r.Rule(u'/wat', endpoint='enter'),
            r.Rule(u'/woop', endpoint='foobar')
        ])
        rv = repr(m)
        self.assert_strict_equal(rv,
            "Map([<Rule '/woop' -> foobar>, <Rule '/wat' -> enter>])")


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(RoutingTestCase))
    return suite
