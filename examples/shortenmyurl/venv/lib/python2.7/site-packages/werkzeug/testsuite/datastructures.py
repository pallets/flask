# -*- coding: utf-8 -*-
"""
    werkzeug.testsuite.datastructures
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests the functionality of the provided Werkzeug
    datastructures.

    TODO:

    -   FileMultiDict
    -   Immutable types undertested
    -   Split up dict tests

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import with_statement

import unittest
import pickle
from contextlib import contextmanager
from copy import copy, deepcopy

from werkzeug import datastructures
from werkzeug._compat import iterkeys, itervalues, iteritems, iterlists, \
     iterlistvalues, text_type, PY2
from werkzeug.testsuite import WerkzeugTestCase
from werkzeug.exceptions import BadRequestKeyError


class NativeItermethodsTestCase(WerkzeugTestCase):
    def test_basic(self):
        @datastructures.native_itermethods(['keys', 'values', 'items'])
        class StupidDict(object):
            def keys(self, multi=1):
                return iter(['a', 'b', 'c'] * multi)

            def values(self, multi=1):
                return iter([1, 2, 3] * multi)

            def items(self, multi=1):
                return iter(zip(iterkeys(self, multi=multi),
                                itervalues(self, multi=multi)))

        d = StupidDict()
        expected_keys = ['a', 'b', 'c']
        expected_values = [1, 2, 3]
        expected_items = list(zip(expected_keys, expected_values))

        self.assert_equal(list(iterkeys(d)), expected_keys)
        self.assert_equal(list(itervalues(d)), expected_values)
        self.assert_equal(list(iteritems(d)), expected_items)

        self.assert_equal(list(iterkeys(d, 2)), expected_keys * 2)
        self.assert_equal(list(itervalues(d, 2)), expected_values * 2)
        self.assert_equal(list(iteritems(d, 2)), expected_items * 2)


class MutableMultiDictBaseTestCase(WerkzeugTestCase):
    storage_class = None

    def test_pickle(self):
        cls = self.storage_class

        for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
            d = cls()
            d.setlist(b'foo', [1, 2, 3, 4])
            d.setlist(b'bar', b'foo bar baz'.split())
            s = pickle.dumps(d, protocol)
            ud = pickle.loads(s)
            self.assert_equal(type(ud), type(d))
            self.assert_equal(ud, d)
            self.assert_equal(pickle.loads(
                s.replace(b'werkzeug.datastructures', b'werkzeug')), d)
            ud[b'newkey'] = b'bla'
            self.assert_not_equal(ud, d)

    def test_basic_interface(self):
        md = self.storage_class()
        assert isinstance(md, dict)

        mapping = [('a', 1), ('b', 2), ('a', 2), ('d', 3),
                   ('a', 1), ('a', 3), ('d', 4), ('c', 3)]
        md = self.storage_class(mapping)

        # simple getitem gives the first value
        self.assert_equal(md['a'], 1)
        self.assert_equal(md['c'], 3)
        with self.assert_raises(KeyError):
            md['e']
        self.assert_equal(md.get('a'), 1)

        # list getitem
        self.assert_equal(md.getlist('a'), [1, 2, 1, 3])
        self.assert_equal(md.getlist('d'), [3, 4])
        # do not raise if key not found
        self.assert_equal(md.getlist('x'), [])

        # simple setitem overwrites all values
        md['a'] = 42
        self.assert_equal(md.getlist('a'), [42])

        # list setitem
        md.setlist('a', [1, 2, 3])
        self.assert_equal(md['a'], 1)
        self.assert_equal(md.getlist('a'), [1, 2, 3])

        # verify that it does not change original lists
        l1 = [1, 2, 3]
        md.setlist('a', l1)
        del l1[:]
        self.assert_equal(md['a'], 1)

        # setdefault, setlistdefault
        self.assert_equal(md.setdefault('u', 23), 23)
        self.assert_equal(md.getlist('u'), [23])
        del md['u']

        md.setlist('u', [-1, -2])

        # delitem
        del md['u']
        with self.assert_raises(KeyError):
            md['u']
        del md['d']
        self.assert_equal(md.getlist('d'), [])

        # keys, values, items, lists
        self.assert_equal(list(sorted(md.keys())), ['a', 'b', 'c'])
        self.assert_equal(list(sorted(iterkeys(md))), ['a', 'b', 'c'])

        self.assert_equal(list(sorted(itervalues(md))), [1, 2, 3])
        self.assert_equal(list(sorted(itervalues(md))), [1, 2, 3])

        self.assert_equal(list(sorted(md.items())),
                          [('a', 1), ('b', 2), ('c', 3)])
        self.assert_equal(list(sorted(md.items(multi=True))),
                          [('a', 1), ('a', 2), ('a', 3), ('b', 2), ('c', 3)])
        self.assert_equal(list(sorted(iteritems(md))),
                          [('a', 1), ('b', 2), ('c', 3)])
        self.assert_equal(list(sorted(iteritems(md, multi=True))),
                          [('a', 1), ('a', 2), ('a', 3), ('b', 2), ('c', 3)])

        self.assert_equal(list(sorted(md.lists())),
                          [('a', [1, 2, 3]), ('b', [2]), ('c', [3])])
        self.assert_equal(list(sorted(iterlists(md))),
                          [('a', [1, 2, 3]), ('b', [2]), ('c', [3])])

        # copy method
        c = md.copy()
        self.assert_equal(c['a'], 1)
        self.assert_equal(c.getlist('a'), [1, 2, 3])

        # copy method 2
        c = copy(md)
        self.assert_equal(c['a'], 1)
        self.assert_equal(c.getlist('a'), [1, 2, 3])
        
        # deepcopy method
        c = md.deepcopy()
        self.assert_equal(c['a'], 1)
        self.assert_equal(c.getlist('a'), [1, 2, 3])
        
        # deepcopy method 2
        c = deepcopy(md)
        self.assert_equal(c['a'], 1)
        self.assert_equal(c.getlist('a'), [1, 2, 3])

        # update with a multidict
        od = self.storage_class([('a', 4), ('a', 5), ('y', 0)])
        md.update(od)
        self.assert_equal(md.getlist('a'), [1, 2, 3, 4, 5])
        self.assert_equal(md.getlist('y'), [0])

        # update with a regular dict
        md = c
        od = {'a': 4, 'y': 0}
        md.update(od)
        self.assert_equal(md.getlist('a'), [1, 2, 3, 4])
        self.assert_equal(md.getlist('y'), [0])

        # pop, poplist, popitem, popitemlist
        self.assert_equal(md.pop('y'), 0)
        assert 'y' not in md
        self.assert_equal(md.poplist('a'), [1, 2, 3, 4])
        assert 'a' not in md
        self.assert_equal(md.poplist('missing'), [])

        # remaining: b=2, c=3
        popped = md.popitem()
        assert popped in [('b', 2), ('c', 3)]
        popped = md.popitemlist()
        assert popped in [('b', [2]), ('c', [3])]

        # type conversion
        md = self.storage_class({'a': '4', 'b': ['2', '3']})
        self.assert_equal(md.get('a', type=int), 4)
        self.assert_equal(md.getlist('b', type=int), [2, 3])

        # repr
        md = self.storage_class([('a', 1), ('a', 2), ('b', 3)])
        assert "('a', 1)" in repr(md)
        assert "('a', 2)" in repr(md)
        assert "('b', 3)" in repr(md)

        # add and getlist
        md.add('c', '42')
        md.add('c', '23')
        self.assert_equal(md.getlist('c'), ['42', '23'])
        md.add('c', 'blah')
        self.assert_equal(md.getlist('c', type=int), [42, 23])

        # setdefault
        md = self.storage_class()
        md.setdefault('x', []).append(42)
        md.setdefault('x', []).append(23)
        self.assert_equal(md['x'], [42, 23])

        # to dict
        md = self.storage_class()
        md['foo'] = 42
        md.add('bar', 1)
        md.add('bar', 2)
        self.assert_equal(md.to_dict(), {'foo': 42, 'bar': 1})
        self.assert_equal(md.to_dict(flat=False), {'foo': [42], 'bar': [1, 2]})

        # popitem from empty dict
        with self.assert_raises(KeyError):
            self.storage_class().popitem()

        with self.assert_raises(KeyError):
            self.storage_class().popitemlist()

        # key errors are of a special type
        with self.assert_raises(BadRequestKeyError):
            self.storage_class()[42]

        # setlist works
        md = self.storage_class()
        md['foo'] = 42
        md.setlist('foo', [1, 2])
        self.assert_equal(md.getlist('foo'), [1, 2])


class ImmutableDictBaseTestCase(WerkzeugTestCase):
    storage_class = None

    def test_follows_dict_interface(self):
        cls = self.storage_class

        data = {'foo': 1, 'bar': 2, 'baz': 3}
        d = cls(data)

        self.assert_equal(d['foo'], 1)
        self.assert_equal(d['bar'], 2)
        self.assert_equal(d['baz'], 3)
        self.assert_equal(sorted(d.keys()), ['bar', 'baz', 'foo'])
        self.assert_true('foo' in d)
        self.assert_true('foox' not in d)
        self.assert_equal(len(d), 3)

    def test_copies_are_mutable(self):
        cls = self.storage_class
        immutable = cls({'a': 1})
        with self.assert_raises(TypeError):
            immutable.pop('a')

        mutable = immutable.copy()
        mutable.pop('a')
        self.assert_true('a' in immutable)
        self.assert_true(mutable is not immutable)
        self.assert_true(copy(immutable) is immutable)

    def test_dict_is_hashable(self):
        cls = self.storage_class
        immutable = cls({'a': 1, 'b': 2})
        immutable2 = cls({'a': 2, 'b': 2})
        x = set([immutable])
        self.assert_true(immutable in x)
        self.assert_true(immutable2 not in x)
        x.discard(immutable)
        self.assert_true(immutable not in x)
        self.assert_true(immutable2 not in x)
        x.add(immutable2)
        self.assert_true(immutable not in x)
        self.assert_true(immutable2 in x)
        x.add(immutable)
        self.assert_true(immutable in x)
        self.assert_true(immutable2 in x)


class ImmutableTypeConversionDictTestCase(ImmutableDictBaseTestCase):
    storage_class = datastructures.ImmutableTypeConversionDict


class ImmutableMultiDictTestCase(ImmutableDictBaseTestCase):
    storage_class = datastructures.ImmutableMultiDict

    def test_multidict_is_hashable(self):
        cls = self.storage_class
        immutable = cls({'a': [1, 2], 'b': 2})
        immutable2 = cls({'a': [1], 'b': 2})
        x = set([immutable])
        self.assert_true(immutable in x)
        self.assert_true(immutable2 not in x)
        x.discard(immutable)
        self.assert_true(immutable not in x)
        self.assert_true(immutable2 not in x)
        x.add(immutable2)
        self.assert_true(immutable not in x)
        self.assert_true(immutable2 in x)
        x.add(immutable)
        self.assert_true(immutable in x)
        self.assert_true(immutable2 in x)


class ImmutableDictTestCase(ImmutableDictBaseTestCase):
    storage_class = datastructures.ImmutableDict


class ImmutableOrderedMultiDictTestCase(ImmutableDictBaseTestCase):
    storage_class = datastructures.ImmutableOrderedMultiDict

    def test_ordered_multidict_is_hashable(self):
        a = self.storage_class([('a', 1), ('b', 1), ('a', 2)])
        b = self.storage_class([('a', 1), ('a', 2), ('b', 1)])
        self.assert_not_equal(hash(a), hash(b))


class MultiDictTestCase(MutableMultiDictBaseTestCase):
    storage_class = datastructures.MultiDict

    def test_multidict_pop(self):
        make_d = lambda: self.storage_class({'foo': [1, 2, 3, 4]})
        d = make_d()
        self.assert_equal(d.pop('foo'), 1)
        assert not d
        d = make_d()
        self.assert_equal(d.pop('foo', 32), 1)
        assert not d
        d = make_d()
        self.assert_equal(d.pop('foos', 32), 32)
        assert d

        with self.assert_raises(KeyError):
            d.pop('foos')

    def test_setlistdefault(self):
        md = self.storage_class()
        self.assert_equal(md.setlistdefault('u', [-1, -2]), [-1, -2])
        self.assert_equal(md.getlist('u'), [-1, -2])
        self.assert_equal(md['u'], -1)

    def test_iter_interfaces(self):
        mapping = [('a', 1), ('b', 2), ('a', 2), ('d', 3),
                   ('a', 1), ('a', 3), ('d', 4), ('c', 3)]
        md = self.storage_class(mapping)
        self.assert_equal(list(zip(md.keys(), md.listvalues())),
                          list(md.lists()))
        self.assert_equal(list(zip(md, iterlistvalues(md))),
                          list(iterlists(md)))
        self.assert_equal(list(zip(iterkeys(md), iterlistvalues(md))),
                          list(iterlists(md)))


class OrderedMultiDictTestCase(MutableMultiDictBaseTestCase):
    storage_class = datastructures.OrderedMultiDict

    def test_ordered_interface(self):
        cls = self.storage_class

        d = cls()
        assert not d
        d.add('foo', 'bar')
        self.assert_equal(len(d), 1)
        d.add('foo', 'baz')
        self.assert_equal(len(d), 1)
        self.assert_equal(list(iteritems(d)), [('foo', 'bar')])
        self.assert_equal(list(d), ['foo'])
        self.assert_equal(list(iteritems(d, multi=True)),
                          [('foo', 'bar'), ('foo', 'baz')])
        del d['foo']
        assert not d
        self.assert_equal(len(d), 0)
        self.assert_equal(list(d), [])

        d.update([('foo', 1), ('foo', 2), ('bar', 42)])
        d.add('foo', 3)
        self.assert_equal(d.getlist('foo'), [1, 2, 3])
        self.assert_equal(d.getlist('bar'), [42])
        self.assert_equal(list(iteritems(d)), [('foo', 1), ('bar', 42)])

        expected = ['foo', 'bar']

        self.assert_sequence_equal(list(d.keys()), expected)
        self.assert_sequence_equal(list(d), expected)
        self.assert_sequence_equal(list(iterkeys(d)), expected)

        self.assert_equal(list(iteritems(d, multi=True)),
                          [('foo', 1), ('foo', 2), ('bar', 42), ('foo', 3)])
        self.assert_equal(len(d), 2)

        self.assert_equal(d.pop('foo'), 1)
        assert d.pop('blafasel', None) is None
        self.assert_equal(d.pop('blafasel', 42), 42)
        self.assert_equal(len(d), 1)
        self.assert_equal(d.poplist('bar'), [42])
        assert not d

        d.get('missingkey') is None

        d.add('foo', 42)
        d.add('foo', 23)
        d.add('bar', 2)
        d.add('foo', 42)
        self.assert_equal(d, datastructures.MultiDict(d))
        id = self.storage_class(d)
        self.assert_equal(d, id)
        d.add('foo', 2)
        assert d != id

        d.update({'blah': [1, 2, 3]})
        self.assert_equal(d['blah'], 1)
        self.assert_equal(d.getlist('blah'), [1, 2, 3])

        # setlist works
        d = self.storage_class()
        d['foo'] = 42
        d.setlist('foo', [1, 2])
        self.assert_equal(d.getlist('foo'), [1, 2])

        with self.assert_raises(BadRequestKeyError):
            d.pop('missing')
        with self.assert_raises(BadRequestKeyError):
            d['missing']

        # popping
        d = self.storage_class()
        d.add('foo', 23)
        d.add('foo', 42)
        d.add('foo', 1)
        self.assert_equal(d.popitem(), ('foo', 23))
        with self.assert_raises(BadRequestKeyError):
            d.popitem()
        assert not d

        d.add('foo', 23)
        d.add('foo', 42)
        d.add('foo', 1)
        self.assert_equal(d.popitemlist(), ('foo', [23, 42, 1]))

        with self.assert_raises(BadRequestKeyError):
            d.popitemlist()

    def test_iterables(self):
        a = datastructures.MultiDict((("key_a", "value_a"),))
        b = datastructures.MultiDict((("key_b", "value_b"),))
        ab = datastructures.CombinedMultiDict((a,b))

        self.assert_equal(sorted(ab.lists()), [('key_a', ['value_a']), ('key_b', ['value_b'])])
        self.assert_equal(sorted(ab.listvalues()), [['value_a'], ['value_b']])
        self.assert_equal(sorted(ab.keys()), ["key_a", "key_b"])

        self.assert_equal(sorted(iterlists(ab)), [('key_a', ['value_a']), ('key_b', ['value_b'])])
        self.assert_equal(sorted(iterlistvalues(ab)), [['value_a'], ['value_b']])
        self.assert_equal(sorted(iterkeys(ab)), ["key_a", "key_b"])


class CombinedMultiDictTestCase(WerkzeugTestCase):
    storage_class = datastructures.CombinedMultiDict

    def test_basic_interface(self):
        d1 = datastructures.MultiDict([('foo', '1')])
        d2 = datastructures.MultiDict([('bar', '2'), ('bar', '3')])
        d = self.storage_class([d1, d2])

        # lookup
        self.assert_equal(d['foo'], '1')
        self.assert_equal(d['bar'], '2')
        self.assert_equal(d.getlist('bar'), ['2', '3'])

        self.assert_equal(sorted(d.items()),
                          [('bar', '2'), ('foo', '1')])
        self.assert_equal(sorted(d.items(multi=True)),
                          [('bar', '2'), ('bar', '3'), ('foo', '1')])
        assert 'missingkey' not in d
        assert 'foo' in d

        # type lookup
        self.assert_equal(d.get('foo', type=int), 1)
        self.assert_equal(d.getlist('bar', type=int), [2, 3])

        # get key errors for missing stuff
        with self.assert_raises(KeyError):
            d['missing']

        # make sure that they are immutable
        with self.assert_raises(TypeError):
            d['foo'] = 'blub'

        # copies are immutable
        d = d.copy()
        with self.assert_raises(TypeError):
            d['foo'] = 'blub'

        # make sure lists merges
        md1 = datastructures.MultiDict((("foo", "bar"),))
        md2 = datastructures.MultiDict((("foo", "blafasel"),))
        x = self.storage_class((md1, md2))
        self.assert_equal(list(iterlists(x)), [('foo', ['bar', 'blafasel'])])


class HeadersTestCase(WerkzeugTestCase):
    storage_class = datastructures.Headers

    def test_basic_interface(self):
        headers = self.storage_class()
        headers.add('Content-Type', 'text/plain')
        headers.add('X-Foo', 'bar')
        assert 'x-Foo' in headers
        assert 'Content-type' in headers

        headers['Content-Type'] = 'foo/bar'
        self.assert_equal(headers['Content-Type'], 'foo/bar')
        self.assert_equal(len(headers.getlist('Content-Type')), 1)

        # list conversion
        self.assert_equal(headers.to_wsgi_list(), [
            ('Content-Type', 'foo/bar'),
            ('X-Foo', 'bar')
        ])
        self.assert_equal(str(headers), (
            "Content-Type: foo/bar\r\n"
            "X-Foo: bar\r\n"
            "\r\n"))
        self.assert_equal(str(self.storage_class()), "\r\n")

        # extended add
        headers.add('Content-Disposition', 'attachment', filename='foo')
        self.assert_equal(headers['Content-Disposition'],
                          'attachment; filename=foo')

        headers.add('x', 'y', z='"')
        self.assert_equal(headers['x'], r'y; z="\""')

    def test_defaults_and_conversion(self):
        # defaults
        headers = self.storage_class([
            ('Content-Type', 'text/plain'),
            ('X-Foo',        'bar'),
            ('X-Bar',        '1'),
            ('X-Bar',        '2')
        ])
        self.assert_equal(headers.getlist('x-bar'), ['1', '2'])
        self.assert_equal(headers.get('x-Bar'), '1')
        self.assert_equal(headers.get('Content-Type'), 'text/plain')

        self.assert_equal(headers.setdefault('X-Foo', 'nope'), 'bar')
        self.assert_equal(headers.setdefault('X-Bar', 'nope'), '1')
        self.assert_equal(headers.setdefault('X-Baz', 'quux'), 'quux')
        self.assert_equal(headers.setdefault('X-Baz', 'nope'), 'quux')
        headers.pop('X-Baz')

        # type conversion
        self.assert_equal(headers.get('x-bar', type=int), 1)
        self.assert_equal(headers.getlist('x-bar', type=int), [1, 2])

        # list like operations
        self.assert_equal(headers[0], ('Content-Type', 'text/plain'))
        self.assert_equal(headers[:1], self.storage_class([('Content-Type', 'text/plain')]))
        del headers[:2]
        del headers[-1]
        self.assert_equal(headers, self.storage_class([('X-Bar', '1')]))

    def test_copying(self):
        a = self.storage_class([('foo', 'bar')])
        b = a.copy()
        a.add('foo', 'baz')
        self.assert_equal(a.getlist('foo'), ['bar', 'baz'])
        self.assert_equal(b.getlist('foo'), ['bar'])

    def test_popping(self):
        headers = self.storage_class([('a', 1)])
        self.assert_equal(headers.pop('a'), 1)
        self.assert_equal(headers.pop('b', 2), 2)

        with self.assert_raises(KeyError):
            headers.pop('c')

    def test_set_arguments(self):
        a = self.storage_class()
        a.set('Content-Disposition', 'useless')
        a.set('Content-Disposition', 'attachment', filename='foo')
        self.assert_equal(a['Content-Disposition'], 'attachment; filename=foo')

    def test_reject_newlines(self):
        h = self.storage_class()

        for variation in 'foo\nbar', 'foo\r\nbar', 'foo\rbar':
            with self.assert_raises(ValueError):
                h['foo'] = variation
            with self.assert_raises(ValueError):
                h.add('foo', variation)
            with self.assert_raises(ValueError):
                h.add('foo', 'test', option=variation)
            with self.assert_raises(ValueError):
                h.set('foo', variation)
            with self.assert_raises(ValueError):
                h.set('foo', 'test', option=variation)

    def test_slicing(self):
        # there's nothing wrong with these being native strings
        # Headers doesn't care about the data types
        h = self.storage_class()
        h.set('X-Foo-Poo', 'bleh')
        h.set('Content-Type', 'application/whocares')
        h.set('X-Forwarded-For', '192.168.0.123')
        h[:] = [(k, v) for k, v in h if k.startswith(u'X-')]
        self.assert_equal(list(h), [
            ('X-Foo-Poo', 'bleh'),
            ('X-Forwarded-For', '192.168.0.123')
        ])

    def test_bytes_operations(self):
        h = self.storage_class()
        h.set('X-Foo-Poo', 'bleh')
        h.set('X-Whoops', b'\xff')

        self.assert_equal(h.get('x-foo-poo', as_bytes=True), b'bleh')
        self.assert_equal(h.get('x-whoops', as_bytes=True), b'\xff')

    def test_to_wsgi_list(self):
        h = self.storage_class()
        h.set(u'Key', u'Value')
        for key, value in h.to_wsgi_list():
            if PY2:
                self.assert_strict_equal(key, b'Key')
                self.assert_strict_equal(value, b'Value')
            else:
                self.assert_strict_equal(key, u'Key')
                self.assert_strict_equal(value, u'Value')



class EnvironHeadersTestCase(WerkzeugTestCase):
    storage_class = datastructures.EnvironHeaders

    def test_basic_interface(self):
        # this happens in multiple WSGI servers because they
        # use a vary naive way to convert the headers;
        broken_env = {
            'HTTP_CONTENT_TYPE':        'text/html',
            'CONTENT_TYPE':             'text/html',
            'HTTP_CONTENT_LENGTH':      '0',
            'CONTENT_LENGTH':           '0',
            'HTTP_ACCEPT':              '*',
            'wsgi.version':             (1, 0)
        }
        headers = self.storage_class(broken_env)
        assert headers
        self.assert_equal(len(headers), 3)
        self.assert_equal(sorted(headers), [
            ('Accept', '*'),
            ('Content-Length', '0'),
            ('Content-Type', 'text/html')
        ])
        assert not self.storage_class({'wsgi.version': (1, 0)})
        self.assert_equal(len(self.storage_class({'wsgi.version': (1, 0)})), 0)

    def test_return_type_is_unicode(self):
        # environ contains native strings; we return unicode
        headers = self.storage_class({
            'HTTP_FOO': '\xe2\x9c\x93',
            'CONTENT_TYPE': 'text/plain',
        })
        self.assert_equal(headers['Foo'], u"\xe2\x9c\x93")
        assert isinstance(headers['Foo'], text_type)
        assert isinstance(headers['Content-Type'], text_type)
        iter_output = dict(iter(headers))
        self.assert_equal(iter_output['Foo'], u"\xe2\x9c\x93")
        assert isinstance(iter_output['Foo'], text_type)
        assert isinstance(iter_output['Content-Type'], text_type)

    def test_bytes_operations(self):
        foo_val = '\xff'
        h = self.storage_class({
            'HTTP_X_FOO': foo_val
        })

        self.assert_equal(h.get('x-foo', as_bytes=True), b'\xff')
        self.assert_equal(h.get('x-foo'), u'\xff')


class HeaderSetTestCase(WerkzeugTestCase):
    storage_class = datastructures.HeaderSet

    def test_basic_interface(self):
        hs = self.storage_class()
        hs.add('foo')
        hs.add('bar')
        assert 'Bar' in hs
        self.assert_equal(hs.find('foo'), 0)
        self.assert_equal(hs.find('BAR'), 1)
        assert hs.find('baz') < 0
        hs.discard('missing')
        hs.discard('foo')
        assert hs.find('foo') < 0
        self.assert_equal(hs.find('bar'), 0)

        with self.assert_raises(IndexError):
            hs.index('missing')

        self.assert_equal(hs.index('bar'), 0)
        assert hs
        hs.clear()
        assert not hs


class ImmutableListTestCase(WerkzeugTestCase):
    storage_class = datastructures.ImmutableList

    def test_list_hashable(self):
        t = (1, 2, 3, 4)
        l = self.storage_class(t)
        self.assert_equal(hash(t), hash(l))
        self.assert_not_equal(t, l)


def make_call_asserter(assert_equal_func, func=None):
    """Utility to assert a certain number of function calls.

    >>> assert_calls, func = make_call_asserter(self.assert_equal)
    >>> with assert_calls(2):
            func()
            func()
    """

    calls = [0]

    @contextmanager
    def asserter(count, msg=None):
        calls[0] = 0
        yield
        assert_equal_func(calls[0], count, msg)

    def wrapped(*args, **kwargs):
        calls[0] += 1
        if func is not None:
            return func(*args, **kwargs)

    return asserter, wrapped


class CallbackDictTestCase(WerkzeugTestCase):
    storage_class = datastructures.CallbackDict

    def test_callback_dict_reads(self):
        assert_calls, func = make_call_asserter(self.assert_equal)
        initial = {'a': 'foo', 'b': 'bar'}
        dct = self.storage_class(initial=initial, on_update=func)
        with assert_calls(0, 'callback triggered by read-only method'):
            # read-only methods
            dct['a']
            dct.get('a')
            self.assert_raises(KeyError, lambda: dct['x'])
            'a' in dct
            list(iter(dct))
            dct.copy()
        with assert_calls(0, 'callback triggered without modification'):
            # methods that may write but don't
            dct.pop('z', None)
            dct.setdefault('a')

    def test_callback_dict_writes(self):
        assert_calls, func = make_call_asserter(self.assert_equal)
        initial = {'a': 'foo', 'b': 'bar'}
        dct = self.storage_class(initial=initial, on_update=func)
        with assert_calls(8, 'callback not triggered by write method'):
            # always-write methods
            dct['z'] = 123
            dct['z'] = 123  # must trigger again
            del dct['z']
            dct.pop('b', None)
            dct.setdefault('x')
            dct.popitem()
            dct.update([])
            dct.clear()
        with assert_calls(0, 'callback triggered by failed del'):
            self.assert_raises(KeyError, lambda: dct.__delitem__('x'))
        with assert_calls(0, 'callback triggered by failed pop'):
            self.assert_raises(KeyError, lambda: dct.pop('x'))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MultiDictTestCase))
    suite.addTest(unittest.makeSuite(OrderedMultiDictTestCase))
    suite.addTest(unittest.makeSuite(CombinedMultiDictTestCase))
    suite.addTest(unittest.makeSuite(ImmutableTypeConversionDictTestCase))
    suite.addTest(unittest.makeSuite(ImmutableMultiDictTestCase))
    suite.addTest(unittest.makeSuite(ImmutableDictTestCase))
    suite.addTest(unittest.makeSuite(ImmutableOrderedMultiDictTestCase))
    suite.addTest(unittest.makeSuite(HeadersTestCase))
    suite.addTest(unittest.makeSuite(EnvironHeadersTestCase))
    suite.addTest(unittest.makeSuite(HeaderSetTestCase))
    suite.addTest(unittest.makeSuite(NativeItermethodsTestCase))
    suite.addTest(unittest.makeSuite(CallbackDictTestCase))
    return suite
