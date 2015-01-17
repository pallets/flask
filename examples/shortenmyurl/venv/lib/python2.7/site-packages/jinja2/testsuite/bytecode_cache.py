# -*- coding: utf-8 -*-
"""
    jinja2.testsuite.bytecode_cache
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test bytecode caching

    :copyright: (c) 2010 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
import unittest

from jinja2.testsuite import JinjaTestCase, package_loader

from jinja2 import Environment
from jinja2.bccache import FileSystemBytecodeCache
from jinja2.exceptions import TemplateNotFound

bytecode_cache = FileSystemBytecodeCache()
env = Environment(
    loader=package_loader,
    bytecode_cache=bytecode_cache,
)


class ByteCodeCacheTestCase(JinjaTestCase):

    def test_simple(self):
        tmpl = env.get_template('test.html')
        assert tmpl.render().strip() == 'BAR'
        self.assert_raises(TemplateNotFound, env.get_template, 'missing.html')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ByteCodeCacheTestCase))
    return suite
