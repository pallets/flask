"""Easy install Tests
"""
import sys
import os
import shutil
import tempfile
import unittest
import site
import contextlib
import textwrap
import tarfile
import logging
import distutils.core

from setuptools.compat import StringIO, BytesIO, next, urlparse
from setuptools.sandbox import run_setup, SandboxViolation
from setuptools.command.easy_install import (
    easy_install, fix_jython_executable, get_script_args, nt_quote_arg)
from setuptools.command.easy_install import PthDistributions
from setuptools.command import easy_install as easy_install_pkg
from setuptools.dist import Distribution
from pkg_resources import working_set, VersionConflict
from pkg_resources import Distribution as PRDistribution
import setuptools.tests.server
import pkg_resources
from .py26compat import skipIf

class FakeDist(object):
    def get_entry_map(self, group):
        if group != 'console_scripts':
            return {}
        return {'name': 'ep'}

    def as_requirement(self):
        return 'spec'

WANTED = """\
#!%s
# EASY-INSTALL-ENTRY-SCRIPT: 'spec','console_scripts','name'
__requires__ = 'spec'
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.exit(
        load_entry_point('spec', 'console_scripts', 'name')()
    )
""" % nt_quote_arg(fix_jython_executable(sys.executable, ""))

SETUP_PY = """\
from setuptools import setup

setup(name='foo')
"""

class TestEasyInstallTest(unittest.TestCase):

    def test_install_site_py(self):
        dist = Distribution()
        cmd = easy_install(dist)
        cmd.sitepy_installed = False
        cmd.install_dir = tempfile.mkdtemp()
        try:
            cmd.install_site_py()
            sitepy = os.path.join(cmd.install_dir, 'site.py')
            self.assertTrue(os.path.exists(sitepy))
        finally:
            shutil.rmtree(cmd.install_dir)

    def test_get_script_args(self):
        dist = FakeDist()

        old_platform = sys.platform
        try:
            name, script = [i for i in next(get_script_args(dist))][0:2]
        finally:
            sys.platform = old_platform

        self.assertEqual(script, WANTED)

    def test_no_find_links(self):
        # new option '--no-find-links', that blocks find-links added at
        # the project level
        dist = Distribution()
        cmd = easy_install(dist)
        cmd.check_pth_processing = lambda: True
        cmd.no_find_links = True
        cmd.find_links = ['link1', 'link2']
        cmd.install_dir = os.path.join(tempfile.mkdtemp(), 'ok')
        cmd.args = ['ok']
        cmd.ensure_finalized()
        self.assertEqual(cmd.package_index.scanned_urls, {})

        # let's try without it (default behavior)
        cmd = easy_install(dist)
        cmd.check_pth_processing = lambda: True
        cmd.find_links = ['link1', 'link2']
        cmd.install_dir = os.path.join(tempfile.mkdtemp(), 'ok')
        cmd.args = ['ok']
        cmd.ensure_finalized()
        keys = sorted(cmd.package_index.scanned_urls.keys())
        self.assertEqual(keys, ['link1', 'link2'])


class TestPTHFileWriter(unittest.TestCase):
    def test_add_from_cwd_site_sets_dirty(self):
        '''a pth file manager should set dirty
        if a distribution is in site but also the cwd
        '''
        pth = PthDistributions('does-not_exist', [os.getcwd()])
        self.assertTrue(not pth.dirty)
        pth.add(PRDistribution(os.getcwd()))
        self.assertTrue(pth.dirty)

    def test_add_from_site_is_ignored(self):
        if os.name != 'nt':
            location = '/test/location/does-not-have-to-exist'
        else:
            location = 'c:\\does_not_exist'
        pth = PthDistributions('does-not_exist', [location, ])
        self.assertTrue(not pth.dirty)
        pth.add(PRDistribution(location))
        self.assertTrue(not pth.dirty)


class TestUserInstallTest(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        setup = os.path.join(self.dir, 'setup.py')
        f = open(setup, 'w')
        f.write(SETUP_PY)
        f.close()
        self.old_cwd = os.getcwd()
        os.chdir(self.dir)

        self.old_enable_site = site.ENABLE_USER_SITE
        self.old_file = easy_install_pkg.__file__
        self.old_base = site.USER_BASE
        site.USER_BASE = tempfile.mkdtemp()
        self.old_site = site.USER_SITE
        site.USER_SITE = tempfile.mkdtemp()
        easy_install_pkg.__file__ = site.USER_SITE

    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.dir)

        shutil.rmtree(site.USER_BASE)
        shutil.rmtree(site.USER_SITE)
        site.USER_BASE = self.old_base
        site.USER_SITE = self.old_site
        site.ENABLE_USER_SITE = self.old_enable_site
        easy_install_pkg.__file__ = self.old_file

    def test_user_install_implied(self):
        site.ENABLE_USER_SITE = True # disabled sometimes
        #XXX: replace with something meaningfull
        dist = Distribution()
        dist.script_name = 'setup.py'
        cmd = easy_install(dist)
        cmd.args = ['py']
        cmd.ensure_finalized()
        self.assertTrue(cmd.user, 'user should be implied')

    def test_multiproc_atexit(self):
        try:
            __import__('multiprocessing')
        except ImportError:
            # skip the test if multiprocessing is not available
            return

        log = logging.getLogger('test_easy_install')
        logging.basicConfig(level=logging.INFO, stream=sys.stderr)
        log.info('this should not break')

    def test_user_install_not_implied_without_usersite_enabled(self):
        site.ENABLE_USER_SITE = False # usually enabled
        #XXX: replace with something meaningfull
        dist = Distribution()
        dist.script_name = 'setup.py'
        cmd = easy_install(dist)
        cmd.args = ['py']
        cmd.initialize_options()
        self.assertFalse(cmd.user, 'NOT user should be implied')

    def test_local_index(self):
        # make sure the local index is used
        # when easy_install looks for installed
        # packages
        new_location = tempfile.mkdtemp()
        target = tempfile.mkdtemp()
        egg_file = os.path.join(new_location, 'foo-1.0.egg-info')
        f = open(egg_file, 'w')
        try:
            f.write('Name: foo\n')
        finally:
            f.close()

        sys.path.append(target)
        old_ppath = os.environ.get('PYTHONPATH')
        os.environ['PYTHONPATH'] = os.path.pathsep.join(sys.path)
        try:
            dist = Distribution()
            dist.script_name = 'setup.py'
            cmd = easy_install(dist)
            cmd.install_dir = target
            cmd.args = ['foo']
            cmd.ensure_finalized()
            cmd.local_index.scan([new_location])
            res = cmd.easy_install('foo')
            actual = os.path.normcase(os.path.realpath(res.location))
            expected = os.path.normcase(os.path.realpath(new_location))
            self.assertEqual(actual, expected)
        finally:
            sys.path.remove(target)
            for basedir in [new_location, target, ]:
                if not os.path.exists(basedir) or not os.path.isdir(basedir):
                    continue
                try:
                    shutil.rmtree(basedir)
                except:
                    pass
            if old_ppath is not None:
                os.environ['PYTHONPATH'] = old_ppath
            else:
                del os.environ['PYTHONPATH']

    def test_setup_requires(self):
        """Regression test for Distribute issue #318

        Ensure that a package with setup_requires can be installed when
        setuptools is installed in the user site-packages without causing a
        SandboxViolation.
        """

        test_pkg = create_setup_requires_package(self.dir)
        test_setup_py = os.path.join(test_pkg, 'setup.py')

        try:
            with quiet_context():
                with reset_setup_stop_context():
                    run_setup(test_setup_py, ['install'])
        except SandboxViolation:
            self.fail('Installation caused SandboxViolation')
        except IndexError:
            # Test fails in some cases due to bugs in Python
            # See https://bitbucket.org/pypa/setuptools/issue/201
            pass


class TestSetupRequires(unittest.TestCase):

    def test_setup_requires_honors_fetch_params(self):
        """
        When easy_install installs a source distribution which specifies
        setup_requires, it should honor the fetch parameters (such as
        allow-hosts, index-url, and find-links).
        """
        # set up a server which will simulate an alternate package index.
        p_index = setuptools.tests.server.MockServer()
        p_index.start()
        netloc = 1
        p_index_loc = urlparse(p_index.url)[netloc]
        if p_index_loc.endswith(':0'):
            # Some platforms (Jython) don't find a port to which to bind,
            #  so skip this test for them.
            return
        with quiet_context():
            # create an sdist that has a build-time dependency.
            with TestSetupRequires.create_sdist() as dist_file:
                with tempdir_context() as temp_install_dir:
                    with environment_context(PYTHONPATH=temp_install_dir):
                        ei_params = ['--index-url', p_index.url,
                            '--allow-hosts', p_index_loc,
                            '--exclude-scripts', '--install-dir', temp_install_dir,
                            dist_file]
                        with reset_setup_stop_context():
                            with argv_context(['easy_install']):
                                # attempt to install the dist. It should fail because
                                #  it doesn't exist.
                                self.assertRaises(SystemExit,
                                    easy_install_pkg.main, ei_params)
        # there should have been two or three requests to the server
        #  (three happens on Python 3.3a)
        self.assertTrue(2 <= len(p_index.requests) <= 3)
        self.assertEqual(p_index.requests[0].path, '/does-not-exist/')

    @staticmethod
    @contextlib.contextmanager
    def create_sdist():
        """
        Return an sdist with a setup_requires dependency (of something that
        doesn't exist)
        """
        with tempdir_context() as dir:
            dist_path = os.path.join(dir, 'setuptools-test-fetcher-1.0.tar.gz')
            make_trivial_sdist(
                dist_path,
                textwrap.dedent("""
                    import setuptools
                    setuptools.setup(
                        name="setuptools-test-fetcher",
                        version="1.0",
                        setup_requires = ['does-not-exist'],
                    )
                """).lstrip())
            yield dist_path

    def test_setup_requires_overrides_version_conflict(self):
        """
        Regression test for issue #323.

        Ensures that a distribution's setup_requires requirements can still be
        installed and used locally even if a conflicting version of that
        requirement is already on the path.
        """

        pr_state = pkg_resources.__getstate__()
        fake_dist = PRDistribution('does-not-matter', project_name='foobar',
                                   version='0.0')
        working_set.add(fake_dist)

        try:
            with tempdir_context() as temp_dir:
                test_pkg = create_setup_requires_package(temp_dir)
                test_setup_py = os.path.join(test_pkg, 'setup.py')
                with quiet_context() as (stdout, stderr):
                    with reset_setup_stop_context():
                        try:
                            # Don't even need to install the package, just
                            # running the setup.py at all is sufficient
                            run_setup(test_setup_py, ['--name'])
                        except VersionConflict:
                            self.fail('Installing setup.py requirements '
                                'caused a VersionConflict')

                lines = stdout.readlines()
                self.assertTrue(len(lines) > 0)
                self.assertTrue(lines[-1].strip(), 'test_pkg')
        finally:
            pkg_resources.__setstate__(pr_state)


def create_setup_requires_package(path):
    """Creates a source tree under path for a trivial test package that has a
    single requirement in setup_requires--a tarball for that requirement is
    also created and added to the dependency_links argument.
    """

    test_setup_attrs = {
        'name': 'test_pkg', 'version': '0.0',
        'setup_requires': ['foobar==0.1'],
        'dependency_links': [os.path.abspath(path)]
    }

    test_pkg = os.path.join(path, 'test_pkg')
    test_setup_py = os.path.join(test_pkg, 'setup.py')
    os.mkdir(test_pkg)

    f = open(test_setup_py, 'w')
    f.write(textwrap.dedent("""\
        import setuptools
        setuptools.setup(**%r)
    """ % test_setup_attrs))
    f.close()

    foobar_path = os.path.join(path, 'foobar-0.1.tar.gz')
    make_trivial_sdist(
        foobar_path,
        textwrap.dedent("""\
            import setuptools
            setuptools.setup(
                name='foobar',
                version='0.1'
            )
        """))

    return test_pkg


def make_trivial_sdist(dist_path, setup_py):
    """Create a simple sdist tarball at dist_path, containing just a
    setup.py, the contents of which are provided by the setup_py string.
    """

    setup_py_file = tarfile.TarInfo(name='setup.py')
    try:
        # Python 3 (StringIO gets converted to io module)
        MemFile = BytesIO
    except AttributeError:
        MemFile = StringIO
    setup_py_bytes = MemFile(setup_py.encode('utf-8'))
    setup_py_file.size = len(setup_py_bytes.getvalue())
    dist = tarfile.open(dist_path, 'w:gz')
    try:
        dist.addfile(setup_py_file, fileobj=setup_py_bytes)
    finally:
        dist.close()


@contextlib.contextmanager
def tempdir_context(cd=lambda dir:None):
    temp_dir = tempfile.mkdtemp()
    orig_dir = os.getcwd()
    try:
        cd(temp_dir)
        yield temp_dir
    finally:
        cd(orig_dir)
        shutil.rmtree(temp_dir)

@contextlib.contextmanager
def environment_context(**updates):
    old_env = os.environ.copy()
    os.environ.update(updates)
    try:
        yield
    finally:
        for key in updates:
            del os.environ[key]
        os.environ.update(old_env)

@contextlib.contextmanager
def argv_context(repl):
    old_argv = sys.argv[:]
    sys.argv[:] = repl
    yield
    sys.argv[:] = old_argv

@contextlib.contextmanager
def reset_setup_stop_context():
    """
    When the setuptools tests are run using setup.py test, and then
    one wants to invoke another setup() command (such as easy_install)
    within those tests, it's necessary to reset the global variable
    in distutils.core so that the setup() command will run naturally.
    """
    setup_stop_after = distutils.core._setup_stop_after
    distutils.core._setup_stop_after = None
    yield
    distutils.core._setup_stop_after = setup_stop_after


@contextlib.contextmanager
def quiet_context():
    """
    Redirect stdout/stderr to StringIO objects to prevent console output from
    distutils commands.
    """

    old_stdout = sys.stdout
    old_stderr = sys.stderr
    new_stdout = sys.stdout = StringIO()
    new_stderr = sys.stderr = StringIO()
    try:
        yield new_stdout, new_stderr
    finally:
        new_stdout.seek(0)
        new_stderr.seek(0)
        sys.stdout = old_stdout
        sys.stderr = old_stderr
