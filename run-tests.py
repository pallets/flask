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

        all_results = []
        for testcase, testname in find_all_tests_with_name():
            if testname.endswith('.' + name):
                all_results.append((testcase, testname))

        if len(all_results) == 1:
            return all_results[0][0]
        elif not len(all_results):
            error = 'could not find testcase "%s"' % name
        else:
            error = 'Too many matches: for "%s"\n%s' % \
                (name, '\n'.join('  - ' + n for c, n in all_results))

        print >> sys.stderr, 'Error: %s' % error
        sys.exit(1)


unittest.main(testLoader=BetterLoader(), defaultTest='suite')
