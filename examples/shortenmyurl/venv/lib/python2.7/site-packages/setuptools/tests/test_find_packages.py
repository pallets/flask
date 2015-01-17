"""Tests for setuptools.find_packages()."""
import os
import sys
import shutil
import tempfile
import unittest
import platform

import setuptools
from setuptools import find_packages
from setuptools.tests.py26compat import skipIf

find_420_packages = setuptools.PEP420PackageFinder.find

def has_symlink():
    bad_symlink = (
        # Windows symlink directory detection is broken on Python 3.2
        platform.system() == 'Windows' and sys.version_info[:2] == (3,2)
    )
    return hasattr(os, 'symlink') and not bad_symlink

class TestFindPackages(unittest.TestCase):

    def setUp(self):
        self.dist_dir = tempfile.mkdtemp()
        self._make_pkg_structure()

    def tearDown(self):
        shutil.rmtree(self.dist_dir)

    def _make_pkg_structure(self):
        """Make basic package structure.

        dist/
            docs/
                conf.py
            pkg/
                __pycache__/
                nspkg/
                    mod.py
                subpkg/
                    assets/
                        asset
                    __init__.py
            setup.py

        """
        self.docs_dir = self._mkdir('docs', self.dist_dir)
        self._touch('conf.py', self.docs_dir)
        self.pkg_dir = self._mkdir('pkg', self.dist_dir)
        self._mkdir('__pycache__', self.pkg_dir)
        self.ns_pkg_dir = self._mkdir('nspkg', self.pkg_dir)
        self._touch('mod.py', self.ns_pkg_dir)
        self.sub_pkg_dir = self._mkdir('subpkg', self.pkg_dir)
        self.asset_dir = self._mkdir('assets', self.sub_pkg_dir)
        self._touch('asset', self.asset_dir)
        self._touch('__init__.py', self.sub_pkg_dir)
        self._touch('setup.py', self.dist_dir)

    def _mkdir(self, path, parent_dir=None):
        if parent_dir:
            path = os.path.join(parent_dir, path)
        os.mkdir(path)
        return path

    def _touch(self, path, dir_=None):
        if dir_:
            path = os.path.join(dir_, path)
        fp = open(path, 'w')
        fp.close()
        return path

    def test_regular_package(self):
        self._touch('__init__.py', self.pkg_dir)
        packages = find_packages(self.dist_dir)
        self.assertEqual(packages, ['pkg', 'pkg.subpkg'])

    def test_exclude(self):
        self._touch('__init__.py', self.pkg_dir)
        packages = find_packages(self.dist_dir, exclude=('pkg.*',))
        assert packages == ['pkg']

    def test_include_excludes_other(self):
        """
        If include is specified, other packages should be excluded.
        """
        self._touch('__init__.py', self.pkg_dir)
        alt_dir = self._mkdir('other_pkg', self.dist_dir)
        self._touch('__init__.py', alt_dir)
        packages = find_packages(self.dist_dir, include=['other_pkg'])
        self.assertEqual(packages, ['other_pkg'])

    def test_dir_with_dot_is_skipped(self):
        shutil.rmtree(os.path.join(self.dist_dir, 'pkg/subpkg/assets'))
        data_dir = self._mkdir('some.data', self.pkg_dir)
        self._touch('__init__.py', data_dir)
        self._touch('file.dat', data_dir)
        packages = find_packages(self.dist_dir)
        self.assertTrue('pkg.some.data' not in packages)

    def test_dir_with_packages_in_subdir_is_excluded(self):
        """
        Ensure that a package in a non-package such as build/pkg/__init__.py
        is excluded.
        """
        build_dir = self._mkdir('build', self.dist_dir)
        build_pkg_dir = self._mkdir('pkg', build_dir)
        self._touch('__init__.py', build_pkg_dir)
        packages = find_packages(self.dist_dir)
        self.assertTrue('build.pkg' not in packages)

    @skipIf(not has_symlink(), 'Symlink support required')
    def test_symlinked_packages_are_included(self):
        """
        A symbolically-linked directory should be treated like any other
        directory when matched as a package.

        Create a link from lpkg -> pkg.
        """
        self._touch('__init__.py', self.pkg_dir)
        linked_pkg = os.path.join(self.dist_dir, 'lpkg')
        os.symlink('pkg', linked_pkg)
        assert os.path.isdir(linked_pkg)
        packages = find_packages(self.dist_dir)
        self.assertTrue('lpkg' in packages)

    def _assert_packages(self, actual, expected):
        self.assertEqual(set(actual), set(expected))

    def test_pep420_ns_package(self):
        packages = find_420_packages(
            self.dist_dir, include=['pkg*'], exclude=['pkg.subpkg.assets'])
        self._assert_packages(packages, ['pkg', 'pkg.nspkg', 'pkg.subpkg'])

    def test_pep420_ns_package_no_includes(self):
        packages = find_420_packages(
            self.dist_dir, exclude=['pkg.subpkg.assets'])
        self._assert_packages(packages, ['docs', 'pkg', 'pkg.nspkg', 'pkg.subpkg'])

    def test_pep420_ns_package_no_includes_or_excludes(self):
        packages = find_420_packages(self.dist_dir)
        expected = [
            'docs', 'pkg', 'pkg.nspkg', 'pkg.subpkg', 'pkg.subpkg.assets']
        self._assert_packages(packages, expected)

    def test_regular_package_with_nested_pep420_ns_packages(self):
        self._touch('__init__.py', self.pkg_dir)
        packages = find_420_packages(
            self.dist_dir, exclude=['docs', 'pkg.subpkg.assets'])
        self._assert_packages(packages, ['pkg', 'pkg.nspkg', 'pkg.subpkg'])

    def test_pep420_ns_package_no_non_package_dirs(self):
        shutil.rmtree(self.docs_dir)
        shutil.rmtree(os.path.join(self.dist_dir, 'pkg/subpkg/assets'))
        packages = find_420_packages(self.dist_dir)
        self._assert_packages(packages, ['pkg', 'pkg.nspkg', 'pkg.subpkg'])
