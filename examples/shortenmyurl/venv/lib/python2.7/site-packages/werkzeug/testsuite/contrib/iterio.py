# -*- coding: utf-8 -*-
"""
    werkzeug.testsuite.iterio
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests the iterio object.

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import unittest
from functools import partial

from werkzeug.testsuite import WerkzeugTestCase
from werkzeug.contrib.iterio import IterIO, greenlet


class IterOTestSuite(WerkzeugTestCase):

    def test_basic_native(self):
        io = IterIO(["Hello", "World", "1", "2", "3"])
        self.assert_equal(io.tell(), 0)
        self.assert_equal(io.read(2), "He")
        self.assert_equal(io.tell(), 2)
        self.assert_equal(io.read(3), "llo")
        self.assert_equal(io.tell(), 5)
        io.seek(0)
        self.assert_equal(io.read(5), "Hello")
        self.assert_equal(io.tell(), 5)
        self.assert_equal(io._buf, "Hello")
        self.assert_equal(io.read(), "World123")
        self.assert_equal(io.tell(), 13)
        io.close()
        assert io.closed

        io = IterIO(["Hello\n", "World!"])
        self.assert_equal(io.readline(), 'Hello\n')
        self.assert_equal(io._buf, 'Hello\n')
        self.assert_equal(io.read(), 'World!')
        self.assert_equal(io._buf, 'Hello\nWorld!')
        self.assert_equal(io.tell(), 12)
        io.seek(0)
        self.assert_equal(io.readlines(), ['Hello\n', 'World!'])

        io = IterIO(["foo\n", "bar"])
        io.seek(-4, 2)
        self.assert_equal(io.read(4), '\nbar')

        self.assert_raises(IOError, io.seek, 2, 100)
        io.close()
        self.assert_raises(ValueError, io.read)

    def test_basic_bytes(self):
        io = IterIO([b"Hello", b"World", b"1", b"2", b"3"])
        self.assert_equal(io.tell(), 0)
        self.assert_equal(io.read(2), b"He")
        self.assert_equal(io.tell(), 2)
        self.assert_equal(io.read(3), b"llo")
        self.assert_equal(io.tell(), 5)
        io.seek(0)
        self.assert_equal(io.read(5), b"Hello")
        self.assert_equal(io.tell(), 5)
        self.assert_equal(io._buf, b"Hello")
        self.assert_equal(io.read(), b"World123")
        self.assert_equal(io.tell(), 13)
        io.close()
        assert io.closed

        io = IterIO([b"Hello\n", b"World!"])
        self.assert_equal(io.readline(), b'Hello\n')
        self.assert_equal(io._buf, b'Hello\n')
        self.assert_equal(io.read(), b'World!')
        self.assert_equal(io._buf, b'Hello\nWorld!')
        self.assert_equal(io.tell(), 12)
        io.seek(0)
        self.assert_equal(io.readlines(), [b'Hello\n', b'World!'])

        io = IterIO([b"foo\n", b"bar"])
        io.seek(-4, 2)
        self.assert_equal(io.read(4), b'\nbar')

        self.assert_raises(IOError, io.seek, 2, 100)
        io.close()
        self.assert_raises(ValueError, io.read)

    def test_basic_unicode(self):
        io = IterIO([u"Hello", u"World", u"1", u"2", u"3"])
        self.assert_equal(io.tell(), 0)
        self.assert_equal(io.read(2), u"He")
        self.assert_equal(io.tell(), 2)
        self.assert_equal(io.read(3), u"llo")
        self.assert_equal(io.tell(), 5)
        io.seek(0)
        self.assert_equal(io.read(5), u"Hello")
        self.assert_equal(io.tell(), 5)
        self.assert_equal(io._buf, u"Hello")
        self.assert_equal(io.read(), u"World123")
        self.assert_equal(io.tell(), 13)
        io.close()
        assert io.closed

        io = IterIO([u"Hello\n", u"World!"])
        self.assert_equal(io.readline(), u'Hello\n')
        self.assert_equal(io._buf, u'Hello\n')
        self.assert_equal(io.read(), u'World!')
        self.assert_equal(io._buf, u'Hello\nWorld!')
        self.assert_equal(io.tell(), 12)
        io.seek(0)
        self.assert_equal(io.readlines(), [u'Hello\n', u'World!'])

        io = IterIO([u"foo\n", u"bar"])
        io.seek(-4, 2)
        self.assert_equal(io.read(4), u'\nbar')

        self.assert_raises(IOError, io.seek, 2, 100)
        io.close()
        self.assert_raises(ValueError, io.read)

    def test_sentinel_cases(self):
        io = IterIO([])
        self.assert_strict_equal(io.read(), '')
        io = IterIO([], b'')
        self.assert_strict_equal(io.read(), b'')
        io = IterIO([], u'')
        self.assert_strict_equal(io.read(), u'')

        io = IterIO([])
        self.assert_strict_equal(io.read(), '')
        io = IterIO([b''])
        self.assert_strict_equal(io.read(), b'')
        io = IterIO([u''])
        self.assert_strict_equal(io.read(), u'')

        io = IterIO([])
        self.assert_strict_equal(io.readline(), '')
        io = IterIO([], b'')
        self.assert_strict_equal(io.readline(), b'')
        io = IterIO([], u'')
        self.assert_strict_equal(io.readline(), u'')

        io = IterIO([])
        self.assert_strict_equal(io.readline(), '')
        io = IterIO([b''])
        self.assert_strict_equal(io.readline(), b'')
        io = IterIO([u''])
        self.assert_strict_equal(io.readline(), u'')


class IterITestSuite(WerkzeugTestCase):

    def test_basic(self):
        def producer(out):
            out.write('1\n')
            out.write('2\n')
            out.flush()
            out.write('3\n')
        iterable = IterIO(producer)
        self.assert_equal(next(iterable), '1\n2\n')
        self.assert_equal(next(iterable), '3\n')
        self.assert_raises(StopIteration, next, iterable)

    def test_sentinel_cases(self):
        def producer_dummy_flush(out):
            out.flush()
        iterable = IterIO(producer_dummy_flush)
        self.assert_strict_equal(next(iterable), '')

        def producer_empty(out):
            pass
        iterable = IterIO(producer_empty)
        self.assert_raises(StopIteration, next, iterable)

        iterable = IterIO(producer_dummy_flush, b'')
        self.assert_strict_equal(next(iterable), b'')
        iterable = IterIO(producer_dummy_flush, u'')
        self.assert_strict_equal(next(iterable), u'')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(IterOTestSuite))
    if greenlet is not None:
        suite.addTest(unittest.makeSuite(IterITestSuite))
    return suite
