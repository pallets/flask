import sys
import unittest
from unittest.loader import TestLoader
from flask.testsuite import suite

common_prefix = suite.__module__ + '.'


def find_all_tests():
    suites = [suite()]
    while suites:
        s = suites.pop()
        try:
            suites.extend(s)
        except TypeError:
            yield s


def find_all_tests_with_name():
    for testcase in find_all_tests():
        yield testcase, '%s.%s.%s' % (
            testcase.__class__.__module__,
            testcase.__class__.__name__,
            testcase._testMethodName
        )


class BetterLoader(TestLoader):

    def loadTestsFromName(self, name, module=None):
        if name == 'suite':
            return suite()
        for testcase, testname in find_all_tests_with_name():
            if testname == name:
                return testcase
            if testname.startswith(common_prefix):
                if testname[len(common_prefix):] == name:
                    return testcase

        all_tests = []
        for testcase, testname in find_all_tests_with_name():
            if testname.endswith('.' + name) or ('.' + name + '.') in testname:
                all_tests.append(testcase)

        if not all_tests:
            print >> sys.stderr, 'Error: could not find test case for "%s"' % name
            sys.exit(1)

        if len(all_tests) == 1:
            return all_tests[0]
        rv = unittest.TestSuite()
        for test in all_tests:
            rv.addTest(test)
        return rv


unittest.main(testLoader=BetterLoader(), defaultTest='suite')
