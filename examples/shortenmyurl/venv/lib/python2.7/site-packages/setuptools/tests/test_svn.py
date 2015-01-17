# -*- coding: utf-8 -*-
"""svn tests"""

import io
import os
import subprocess
import sys
import unittest
from setuptools.tests import environment
from setuptools.compat import unicode, unichr

from setuptools import svn_utils
from setuptools.tests.py26compat import skipIf


def _do_svn_check():
    try:
        subprocess.check_call(["svn", "--version"],
                              shell=(sys.platform == 'win32'))
        return True
    except (OSError, subprocess.CalledProcessError):
        return False
_svn_check = _do_svn_check()


class TestSvnVersion(unittest.TestCase):

    def test_no_svn_found(self):
        path_variable = None
        for env in os.environ:
            if env.lower() == 'path':
                path_variable = env

        if path_variable is None:
            try:
                self.skipTest('Cannot figure out how to modify path')
            except AttributeError:  # PY26 doesn't have this
                return

        old_path = os.environ[path_variable]
        os.environ[path_variable] = ''
        try:
            version = svn_utils.SvnInfo.get_svn_version()
            self.assertEqual(version, '')
        finally:
            os.environ[path_variable] = old_path

    @skipIf(not _svn_check, "No SVN to text, in the first place")
    def test_svn_should_exist(self):
        version = svn_utils.SvnInfo.get_svn_version()
        self.assertNotEqual(version, '')

def _read_utf8_file(path):
    fileobj = None
    try:
        fileobj = io.open(path, 'r', encoding='utf-8')
        data = fileobj.read()
        return data
    finally:
        if fileobj:
            fileobj.close()


class ParserInfoXML(unittest.TestCase):

    def parse_tester(self, svn_name, ext_spaces):
        path = os.path.join('setuptools', 'tests',
                            'svn_data', svn_name + '_info.xml')
        #Remember these are pre-generated to test XML parsing
        #  so these paths might not valid on your system
        example_base = "%s_example" % svn_name

        data = _read_utf8_file(path)

        expected = set([
            ("\\".join((example_base, 'a file')), 'file'),
            ("\\".join((example_base, 'folder')), 'dir'),
            ("\\".join((example_base, 'folder', 'lalala.txt')), 'file'),
            ("\\".join((example_base, 'folder', 'quest.txt')), 'file'),
            ])
        self.assertEqual(set(x for x in svn_utils.parse_dir_entries(data)),
                         expected)

    def test_svn13(self):
        self.parse_tester('svn13', False)

    def test_svn14(self):
        self.parse_tester('svn14', False)

    def test_svn15(self):
        self.parse_tester('svn15', False)

    def test_svn16(self):
        self.parse_tester('svn16', True)

    def test_svn17(self):
        self.parse_tester('svn17', True)

    def test_svn18(self):
        self.parse_tester('svn18', True)

class ParserExternalXML(unittest.TestCase):

    def parse_tester(self, svn_name, ext_spaces):
        path = os.path.join('setuptools', 'tests',
                            'svn_data', svn_name + '_ext_list.xml')
        example_base = svn_name + '_example'
        data = _read_utf8_file(path)

        if ext_spaces:
            folder2 = 'third party2'
            folder3 = 'third party3'
        else:
            folder2 = 'third_party2'
            folder3 = 'third_party3'

        expected = set([
            os.sep.join((example_base, folder2)),
            os.sep.join((example_base, folder3)),
            # folder is third_party大介
            os.sep.join((example_base,
                       unicode('third_party') +
                       unichr(0x5927) + unichr(0x4ecb))),
            os.sep.join((example_base, 'folder', folder2)),
            os.sep.join((example_base, 'folder', folder3)),
            os.sep.join((example_base, 'folder',
                       unicode('third_party') +
                       unichr(0x5927) + unichr(0x4ecb))),
            ])

        expected = set(os.path.normpath(x) for x in expected)
        dir_base = os.sep.join(('C:', 'development', 'svn_example'))
        self.assertEqual(set(x for x
            in svn_utils.parse_externals_xml(data, dir_base)), expected)

    def test_svn15(self):
        self.parse_tester('svn15', False)

    def test_svn16(self):
        self.parse_tester('svn16', True)

    def test_svn17(self):
        self.parse_tester('svn17', True)

    def test_svn18(self):
        self.parse_tester('svn18', True)


class ParseExternal(unittest.TestCase):

    def parse_tester(self, svn_name, ext_spaces):
        path = os.path.join('setuptools', 'tests',
                            'svn_data', svn_name + '_ext_list.txt')
        data = _read_utf8_file(path)

        if ext_spaces:
            expected = set(['third party2', 'third party3',
                            'third party3b', 'third_party'])
        else:
            expected = set(['third_party2', 'third_party3', 'third_party'])

        self.assertEqual(set(x for x in svn_utils.parse_external_prop(data)),
                         expected)

    def test_svn13(self):
        self.parse_tester('svn13', False)

    def test_svn14(self):
        self.parse_tester('svn14', False)

    def test_svn15(self):
        self.parse_tester('svn15', False)

    def test_svn16(self):
        self.parse_tester('svn16', True)

    def test_svn17(self):
        self.parse_tester('svn17', True)

    def test_svn18(self):
        self.parse_tester('svn18', True)


class TestSvn(environment.ZippedEnvironment):

    def setUp(self):
        version = svn_utils.SvnInfo.get_svn_version()
        if not version:  # empty or null
            self.dataname = None
            self.datafile = None
            return

        self.base_version = tuple([int(x) for x in version.split('.')[:2]])

        if self.base_version < (1,3):
            raise ValueError('Insufficient SVN Version %s' % version)
        elif self.base_version >= (1,9):
            #trying the latest version
            self.base_version = (1,8)

        self.dataname = "svn%i%i_example" % self.base_version
        self.datafile = os.path.join('setuptools', 'tests',
                                     'svn_data', self.dataname + ".zip")
        super(TestSvn, self).setUp()

    @skipIf(not _svn_check, "No SVN to text, in the first place")
    def test_revision(self):
        rev = svn_utils.SvnInfo.load('.').get_revision()
        self.assertEqual(rev, 6)

    @skipIf(not _svn_check, "No SVN to text, in the first place")
    def test_entries(self):
        expected = set([
            (os.path.join('a file'), 'file'),
            (os.path.join('folder'), 'dir'),
            (os.path.join('folder', 'lalala.txt'), 'file'),
            (os.path.join('folder', 'quest.txt'), 'file'),
            #The example will have a deleted file (or should)
            #but shouldn't return it
            ])
        info = svn_utils.SvnInfo.load('.')
        self.assertEqual(set(x for x in info.entries), expected)

    @skipIf(not _svn_check, "No SVN to text, in the first place")
    def test_externals(self):
        if self.base_version >= (1,6):
            folder2 = 'third party2'
            folder3 = 'third party3'
        else:
            folder2 = 'third_party2'
            folder3 = 'third_party3'

        expected = set([
            os.path.join(folder2),
            os.path.join(folder3),
            os.path.join('third_party'),
            os.path.join('folder', folder2),
            os.path.join('folder', folder3),
            os.path.join('folder', 'third_party'),
            ])
        info = svn_utils.SvnInfo.load('.')
        self.assertEqual(set([x for x in info.externals]), expected)

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
