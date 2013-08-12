# -*- coding: utf-8 -*-
"""
    flask.testsuite.config
    ~~~~~~~~~~~~~~~~~~~~~~

    Configuration and instances.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import os
import sys
import flask
import pkgutil
import unittest
from contextlib import contextmanager
from flask.testsuite import FlaskTestCase


# config keys used for the ConfigTestCase
TEST_KEY = 'foo'
SECRET_KEY = 'devkey'


class ConfigTestCase(FlaskTestCase):

    def common_object_test(self, app):
        self.assert_equal(app.secret_key, 'devkey')
        self.assert_equal(app.config['TEST_KEY'], 'foo')
        self.assert_not_in('ConfigTestCase', app.config)

    def test_config_from_file(self):
        app = flask.Flask(__name__)
        app.config.from_pyfile(__file__.rsplit('.', 1)[0] + '.py')
        self.common_object_test(app)

    def test_config_from_object(self):
        app = flask.Flask(__name__)
        app.config.from_object(__name__)
        self.common_object_test(app)

    def test_config_from_class(self):
        class Base(object):
            TEST_KEY = 'foo'
        class Test(Base):
            SECRET_KEY = 'devkey'
        app = flask.Flask(__name__)
        app.config.from_object(Test)
        self.common_object_test(app)

    def test_config_from_envvar(self):
        env = os.environ
        try:
            os.environ = {}
            app = flask.Flask(__name__)
            try:
                app.config.from_envvar('FOO_SETTINGS')
            except RuntimeError as e:
                self.assert_true("'FOO_SETTINGS' is not set" in str(e))
            else:
                self.assert_true(0, 'expected exception')
            self.assert_false(app.config.from_envvar('FOO_SETTINGS', silent=True))

            os.environ = {'FOO_SETTINGS': __file__.rsplit('.', 1)[0] + '.py'}
            self.assert_true(app.config.from_envvar('FOO_SETTINGS'))
            self.common_object_test(app)
        finally:
            os.environ = env

    def test_config_from_envvar_missing(self):
        env = os.environ
        try:
            os.environ = {'FOO_SETTINGS': 'missing.cfg'}
            try:
                app = flask.Flask(__name__)
                app.config.from_envvar('FOO_SETTINGS')
            except IOError as e:
                msg = str(e)
                self.assert_true(msg.startswith('[Errno 2] Unable to load configuration '
                                            'file (No such file or directory):'))
                self.assert_true(msg.endswith("missing.cfg'"))
            else:
                self.fail('expected IOError')
            self.assertFalse(app.config.from_envvar('FOO_SETTINGS', silent=True))
        finally:
            os.environ = env

    def test_config_missing(self):
        app = flask.Flask(__name__)
        try:
            app.config.from_pyfile('missing.cfg')
        except IOError as e:
            msg = str(e)
            self.assert_true(msg.startswith('[Errno 2] Unable to load configuration '
                                        'file (No such file or directory):'))
            self.assert_true(msg.endswith("missing.cfg'"))
        else:
            self.assert_true(0, 'expected config')
        self.assert_false(app.config.from_pyfile('missing.cfg', silent=True))

    def test_session_lifetime(self):
        app = flask.Flask(__name__)
        app.config['PERMANENT_SESSION_LIFETIME'] = 42
        self.assert_equal(app.permanent_session_lifetime.seconds, 42)


class LimitedLoaderMockWrapper(object):
    def __init__(self, loader):
        self.loader = loader

    def __getattr__(self, name):
        if name in ('archive', 'get_filename'):
            msg = 'Mocking a loader which does not have `%s.`' % name
            raise AttributeError(msg)
        return getattr(self.loader, name)


@contextmanager
def patch_pkgutil_get_loader(wrapper_class=LimitedLoaderMockWrapper):
    """Patch pkgutil.get_loader to give loader without get_filename or archive.

    This provides for tests where a system has custom loaders, e.g. Google App
    Engine's HardenedModulesHook, which have neither the `get_filename` method
    nor the `archive` attribute.
    """
    old_get_loader = pkgutil.get_loader
    def get_loader(*args, **kwargs):
        return wrapper_class(old_get_loader(*args, **kwargs))
    try:
        pkgutil.get_loader = get_loader
        yield
    finally:
        pkgutil.get_loader = old_get_loader


class InstanceTestCase(FlaskTestCase):

    def test_explicit_instance_paths(self):
        here = os.path.abspath(os.path.dirname(__file__))
        try:
            flask.Flask(__name__, instance_path='instance')
        except ValueError as e:
            self.assert_in('must be absolute', str(e))
        else:
            self.fail('Expected value error')

        app = flask.Flask(__name__, instance_path=here)
        self.assert_equal(app.instance_path, here)

    def test_main_module_paths(self):
        # Test an app with '__main__' as the import name, uses cwd.
        from main_app import app
        here = os.path.abspath(os.getcwd())
        self.assert_equal(app.instance_path, os.path.join(here, 'instance'))
        if 'main_app' in sys.modules:
            del sys.modules['main_app']

    def test_uninstalled_module_paths(self):
        from config_module_app import app
        here = os.path.abspath(os.path.dirname(__file__))
        self.assert_equal(app.instance_path, os.path.join(here, 'test_apps', 'instance'))

    def test_uninstalled_package_paths(self):
        from config_package_app import app
        here = os.path.abspath(os.path.dirname(__file__))
        self.assert_equal(app.instance_path, os.path.join(here, 'test_apps', 'instance'))

    def test_installed_module_paths(self):
        here = os.path.abspath(os.path.dirname(__file__))
        expected_prefix = os.path.join(here, 'test_apps')
        real_prefix, sys.prefix = sys.prefix, expected_prefix
        site_packages = os.path.join(expected_prefix, 'lib', 'python2.5', 'site-packages')
        sys.path.append(site_packages)
        try:
            import site_app
            self.assert_equal(site_app.app.instance_path,
                              os.path.join(expected_prefix, 'var',
                                           'site_app-instance'))
        finally:
            sys.prefix = real_prefix
            sys.path.remove(site_packages)
            if 'site_app' in sys.modules:
                del sys.modules['site_app']

    def test_installed_module_paths_with_limited_loader(self):
        here = os.path.abspath(os.path.dirname(__file__))
        expected_prefix = os.path.join(here, 'test_apps')
        real_prefix, sys.prefix = sys.prefix, expected_prefix
        site_packages = os.path.join(expected_prefix, 'lib', 'python2.5', 'site-packages')
        sys.path.append(site_packages)
        with patch_pkgutil_get_loader():
            try:
                import site_app
                self.assert_equal(site_app.app.instance_path,
                                  os.path.join(expected_prefix, 'var',
                                               'site_app-instance'))
            finally:
                sys.prefix = real_prefix
                sys.path.remove(site_packages)
                if 'site_app' in sys.modules:
                    del sys.modules['site_app']

    def test_installed_package_paths(self):
        here = os.path.abspath(os.path.dirname(__file__))
        expected_prefix = os.path.join(here, 'test_apps')
        real_prefix, sys.prefix = sys.prefix, expected_prefix
        installed_path = os.path.join(expected_prefix, 'path')
        sys.path.append(installed_path)
        try:
            import installed_package
            self.assert_equal(installed_package.app.instance_path,
                              os.path.join(expected_prefix, 'var',
                                           'installed_package-instance'))
        finally:
            sys.prefix = real_prefix
            sys.path.remove(installed_path)
            if 'installed_package' in sys.modules:
                del sys.modules['installed_package']

    def test_installed_package_paths_with_limited_loader(self):
        here = os.path.abspath(os.path.dirname(__file__))
        expected_prefix = os.path.join(here, 'test_apps')
        real_prefix, sys.prefix = sys.prefix, expected_prefix
        installed_path = os.path.join(expected_prefix, 'path')
        sys.path.append(installed_path)
        with patch_pkgutil_get_loader():
            try:
                import installed_package
                self.assert_equal(installed_package.app.instance_path,
                                  os.path.join(expected_prefix, 'var',
                                               'installed_package-instance'))
            finally:
                sys.prefix = real_prefix
                sys.path.remove(installed_path)
                if 'installed_package' in sys.modules:
                    del sys.modules['installed_package']

    def test_prefix_package_paths(self):
        here = os.path.abspath(os.path.dirname(__file__))
        expected_prefix = os.path.join(here, 'test_apps')
        real_prefix, sys.prefix = sys.prefix, expected_prefix
        site_packages = os.path.join(expected_prefix, 'lib', 'python2.5', 'site-packages')
        sys.path.append(site_packages)
        try:
            import site_package
            self.assert_equal(site_package.app.instance_path,
                              os.path.join(expected_prefix, 'var',
                                           'site_package-instance'))
        finally:
            sys.prefix = real_prefix
            sys.path.remove(site_packages)
            if 'site_package' in sys.modules:
                del sys.modules['site_package']

    def test_prefix_package_paths_with_limited_loader(self):
        here = os.path.abspath(os.path.dirname(__file__))
        expected_prefix = os.path.join(here, 'test_apps')
        real_prefix, sys.prefix = sys.prefix, expected_prefix
        site_packages = os.path.join(expected_prefix, 'lib', 'python2.5', 'site-packages')
        sys.path.append(site_packages)
        with patch_pkgutil_get_loader():
            try:
                import site_package
                self.assert_equal(site_package.app.instance_path,
                                  os.path.join(expected_prefix, 'var',
                                               'site_package-instance'))
            finally:
                sys.prefix = real_prefix
                sys.path.remove(site_packages)
                if 'site_package' in sys.modules:
                    del sys.modules['site_package']

    def test_egg_installed_paths(self):
        here = os.path.abspath(os.path.dirname(__file__))
        expected_prefix = os.path.join(here, 'test_apps')
        real_prefix, sys.prefix = sys.prefix, expected_prefix
        site_packages = os.path.join(expected_prefix, 'lib', 'python2.5', 'site-packages')
        egg_path = os.path.join(site_packages, 'SiteEgg.egg')
        sys.path.append(site_packages)
        sys.path.append(egg_path)
        try:
            import site_egg # in SiteEgg.egg
            self.assert_equal(site_egg.app.instance_path,
                              os.path.join(expected_prefix, 'var',
                                           'site_egg-instance'))
        finally:
            sys.prefix = real_prefix
            sys.path.remove(site_packages)
            sys.path.remove(egg_path)
            if 'site_egg' in sys.modules:
                del sys.modules['site_egg']


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ConfigTestCase))
    suite.addTest(unittest.makeSuite(InstanceTestCase))
    return suite
