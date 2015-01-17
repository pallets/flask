# -*- coding: utf-8 -*-
"""
    jinja2.testsuite
    ~~~~~~~~~~~~~~~~

    All the unittests of Jinja2.  These tests can be executed by
    either running run-tests.py using multiple Python versions at
    the same time.

    :copyright: (c) 2010 by the Jinja Team.
    :license: BSD, see LICENSE for more details.
"""
import os
import re
import sys
import unittest
from traceback import format_exception
from jinja2 import loaders
from jinja2._compat import PY2


here = os.path.dirname(os.path.abspath(__file__))

dict_loader = loaders.DictLoader({
    'justdict.html':        'FOO'
})
package_loader = loaders.PackageLoader('jinja2.testsuite.res', 'templates')
filesystem_loader = loaders.FileSystemLoader(here + '/res/templates')
function_loader = loaders.FunctionLoader({'justfunction.html': 'FOO'}.get)
choice_loader = loaders.ChoiceLoader([dict_loader, package_loader])
prefix_loader = loaders.PrefixLoader({
    'a':        filesystem_loader,
    'b':        dict_loader
})


class JinjaTestCase(unittest.TestCase):

    ### use only these methods for testing.  If you need standard
    ### unittest method, wrap them!

    def setup(self):
        pass

    def teardown(self):
        pass

    def setUp(self):
        self.setup()

    def tearDown(self):
        self.teardown()

    def assert_equal(self, a, b):
        return self.assertEqual(a, b)

    def assert_raises(self, *args, **kwargs):
        return self.assertRaises(*args, **kwargs)

    def assert_traceback_matches(self, callback, expected_tb):
        try:
            callback()
        except Exception as e:
            tb = format_exception(*sys.exc_info())
            if re.search(expected_tb.strip(), ''.join(tb)) is None:
                raise self.fail('Traceback did not match:\n\n%s\nexpected:\n%s'
                    % (''.join(tb), expected_tb))
        else:
            self.fail('Expected exception')


def find_all_tests(suite):
    """Yields all the tests and their names from a given suite."""
    suites = [suite]
    while suites:
        s = suites.pop()
        try:
            suites.extend(s)
        except TypeError:
            yield s, '%s.%s.%s' % (
                s.__class__.__module__,
                s.__class__.__name__,
                s._testMethodName
            )


class BetterLoader(unittest.TestLoader):
    """A nicer loader that solves two problems.  First of all we are setting
    up tests from different sources and we're doing this programmatically
    which breaks the default loading logic so this is required anyways.
    Secondly this loader has a nicer interpolation for test names than the
    default one so you can just do ``run-tests.py ViewTestCase`` and it
    will work.
    """

    def getRootSuite(self):
        return suite()

    def loadTestsFromName(self, name, module=None):
        root = self.getRootSuite()
        if name == 'suite':
            return root

        all_tests = []
        for testcase, testname in find_all_tests(root):
            if testname == name or \
               testname.endswith('.' + name) or \
               ('.' + name + '.') in testname or \
               testname.startswith(name + '.'):
                all_tests.append(testcase)

        if not all_tests:
            raise LookupError('could not find test case for "%s"' % name)

        if len(all_tests) == 1:
            return all_tests[0]
        rv = unittest.TestSuite()
        for test in all_tests:
            rv.addTest(test)
        return rv


def suite():
    from jinja2.testsuite import ext, filters, tests, core_tags, \
         loader, inheritance, imports, lexnparse, security, api, \
         regression, debug, utils, bytecode_cache, doctests
    suite = unittest.TestSuite()
    suite.addTest(ext.suite())
    suite.addTest(filters.suite())
    suite.addTest(tests.suite())
    suite.addTest(core_tags.suite())
    suite.addTest(loader.suite())
    suite.addTest(inheritance.suite())
    suite.addTest(imports.suite())
    suite.addTest(lexnparse.suite())
    suite.addTest(security.suite())
    suite.addTest(api.suite())
    suite.addTest(regression.suite())
    suite.addTest(debug.suite())
    suite.addTest(utils.suite())
    suite.addTest(bytecode_cache.suite())

    # doctests will not run on python 3 currently.  Too many issues
    # with that, do not test that on that platform.
    if PY2:
        suite.addTest(doctests.suite())

    return suite


def main():
    """Runs the testsuite as command line application."""
    try:
        unittest.main(testLoader=BetterLoader(), defaultTest='suite')
    except Exception as e:
        print('Error: %s' % e)
