
import os
import sys
import tempfile
import shutil
import unittest

import pkg_resources
import warnings
from setuptools.command import egg_info
from setuptools import svn_utils
from setuptools.tests import environment, test_svn
from setuptools.tests.py26compat import skipIf

ENTRIES_V10 = pkg_resources.resource_string(__name__, 'entries-v10')
"An entries file generated with svn 1.6.17 against the legacy Setuptools repo"


class TestEggInfo(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.mkdir(os.path.join(self.test_dir, '.svn'))

        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.test_dir)

    def _write_entries(self, entries):
        fn = os.path.join(self.test_dir, '.svn', 'entries')
        entries_f = open(fn, 'wb')
        entries_f.write(entries)
        entries_f.close()
   
    @skipIf(not test_svn._svn_check, "No SVN to text, in the first place")
    def test_version_10_format(self):
        """
        """
        #keeping this set for 1.6 is a good check on the get_svn_revision
        #to ensure I return using svnversion what would had been returned
        version_str = svn_utils.SvnInfo.get_svn_version()
        version = [int(x) for x in version_str.split('.')[:2]]
        if version != [1, 6]:
            if hasattr(self, 'skipTest'):
                self.skipTest('')
            else:
                sys.stderr.write('\n   Skipping due to SVN Version\n')
                return

        self._write_entries(ENTRIES_V10)
        rev = egg_info.egg_info.get_svn_revision()
        self.assertEqual(rev, '89000')

    def test_version_10_format_legacy_parser(self):
        """
        """
        path_variable = None
        for env in os.environ:
            if env.lower() == 'path':
                path_variable = env

        if path_variable:
            old_path = os.environ[path_variable]
            os.environ[path_variable] = ''
        #catch_warnings not available until py26
        warning_filters = warnings.filters
        warnings.filters = warning_filters[:]
        try:
            warnings.simplefilter("ignore", DeprecationWarning)
            self._write_entries(ENTRIES_V10)
            rev = egg_info.egg_info.get_svn_revision()
        finally:
            #restore the warning filters
            warnings.filters = warning_filters
            #restore the os path
            if path_variable:
                os.environ[path_variable] = old_path

        self.assertEqual(rev, '89000')

DUMMY_SOURCE_TXT = """CHANGES.txt
CONTRIBUTORS.txt
HISTORY.txt
LICENSE
MANIFEST.in
README.txt
setup.py
dummy/__init__.py
dummy/test.txt
dummy.egg-info/PKG-INFO
dummy.egg-info/SOURCES.txt
dummy.egg-info/dependency_links.txt
dummy.egg-info/top_level.txt"""


class TestSvnDummy(environment.ZippedEnvironment):

    def setUp(self):
        version = svn_utils.SvnInfo.get_svn_version()
        if not version:  # None or Empty
            return None

        self.base_version = tuple([int(x) for x in version.split('.')][:2])

        if not self.base_version:
            raise ValueError('No SVN tools installed')
        elif self.base_version < (1, 3):
            raise ValueError('Insufficient SVN Version %s' % version)
        elif self.base_version >= (1, 9):
            #trying the latest version
            self.base_version = (1, 8)

        self.dataname = "dummy%i%i" % self.base_version
        self.datafile = os.path.join('setuptools', 'tests',
                                     'svn_data', self.dataname + ".zip")
        super(TestSvnDummy, self).setUp()

    @skipIf(not test_svn._svn_check, "No SVN to text, in the first place")
    def test_sources(self):
        code, data = environment.run_setup_py(["sdist"],
                                              pypath=self.old_cwd,
                                              data_stream=1)
        if code:
            raise AssertionError(data)

        sources = os.path.join('dummy.egg-info', 'SOURCES.txt')
        infile = open(sources, 'r')
        try:
            read_contents = infile.read()
        finally:
            infile.close()
            del infile

        self.assertEqual(DUMMY_SOURCE_TXT, read_contents)

        return data


class TestSvnDummyLegacy(environment.ZippedEnvironment):

    def setUp(self):
        self.base_version = (1, 6)
        self.dataname = "dummy%i%i" % self.base_version
        self.datafile = os.path.join('setuptools', 'tests',
                                     'svn_data', self.dataname + ".zip")
        super(TestSvnDummyLegacy, self).setUp()

    def test_sources(self):
        code, data = environment.run_setup_py(["sdist"],
                                              pypath=self.old_cwd,
                                              path="",
                                              data_stream=1)
        if code:
            raise AssertionError(data)

        sources = os.path.join('dummy.egg-info', 'SOURCES.txt')
        infile = open(sources, 'r')
        try:
            read_contents = infile.read()
        finally:
            infile.close()
            del infile

        self.assertEqual(DUMMY_SOURCE_TXT, read_contents)

        return data


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
