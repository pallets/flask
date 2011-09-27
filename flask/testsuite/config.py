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
import unittest
from flask.testsuite import FlaskTestCase


# config keys used for the ConfigTestCase
TEST_KEY = 'foo'
SECRET_KEY = 'devkey'


class ConfigTestCase(FlaskTestCase):

    def common_object_test(self, app):
        self.assert_equal(app.secret_key, 'devkey')
        self.assert_equal(app.config['TEST_KEY'], 'foo')
        self.assert_('ConfigTestCase' not in app.config)

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
            except RuntimeError, e:
                self.assert_("'FOO_SETTINGS' is not set" in str(e))
            else:
                self.assert_(0, 'expected exception')
            self.assert_(not app.config.from_envvar('FOO_SETTINGS', silent=True))

            os.environ = {'FOO_SETTINGS': __file__.rsplit('.', 1)[0] + '.py'}
            self.assert_(app.config.from_envvar('FOO_SETTINGS'))
            self.common_object_test(app)
        finally:
            os.environ = env

    def test_config_missing(self):
        app = flask.Flask(__name__)
        try:
            app.config.from_pyfile('missing.cfg')
        except IOError, e:
            msg = str(e)
            self.assert_(msg.startswith('[Errno 2] Unable to load configuration '
                                        'file (No such file or directory):'))
            self.assert_(msg.endswith("missing.cfg'"))
        else:
            self.assert_(0, 'expected config')
        self.assert_(not app.config.from_pyfile('missing.cfg', silent=True))

    def test_session_lifetime(self):
        app = flask.Flask(__name__)
        app.config['PERMANENT_SESSION_LIFETIME'] = 42
        self.assert_equal(app.permanent_session_lifetime.seconds, 42)


class InstanceTestCase(FlaskTestCase):

    def test_explicit_instance_paths(self):
        here = os.path.abspath(os.path.dirname(__file__))
        try:
            flask.Flask(__name__, instance_path='instance')
        except ValueError, e:
            self.assert_('must be absolute' in str(e))
        else:
            self.fail('Expected value error')

        app = flask.Flask(__name__, instance_path=here)
        self.assert_equal(app.instance_path, here)

    def test_uninstalled_module_paths(self):
        from config_module_app import app
        here = os.path.abspath(os.path.dirname(__file__))
        self.assert_equal(app.instance_path, os.path.join(here, 'test_apps', 'instance'))

    def test_uninstalled_package_paths(self):
        from config_package_app import app
        here = os.path.abspath(os.path.dirname(__file__))
        self.assert_equal(app.instance_path, os.path.join(here, 'test_apps', 'instance'))

    def test_installed_module_paths(self):
        import types
        expected_prefix = os.path.abspath('foo')
        mod = types.ModuleType('myapp')
        mod.__file__ = os.path.join(expected_prefix, 'lib', 'python2.5',
                                    'site-packages', 'myapp.py')
        sys.modules['myapp'] = mod
        try:
            mod.app = flask.Flask(mod.__name__)
            self.assert_equal(mod.app.instance_path,
                             os.path.join(expected_prefix, 'var',
                                          'myapp-instance'))
        finally:
            sys.modules['myapp'] = None

    def test_installed_package_paths(self):
        import types
        expected_prefix = os.path.abspath('foo')
        package_path = os.path.join(expected_prefix, 'lib', 'python2.5',
                                    'site-packages', 'myapp')
        mod = types.ModuleType('myapp')
        mod.__path__ = [package_path]
        mod.__file__ = os.path.join(package_path, '__init__.py')
        sys.modules['myapp'] = mod
        try:
            mod.app = flask.Flask(mod.__name__)
            self.assert_equal(mod.app.instance_path,
                             os.path.join(expected_prefix, 'var',
                                          'myapp-instance'))
        finally:
            sys.modules['myapp'] = None

    def test_prefix_installed_paths(self):
        import types
        expected_prefix = os.path.abspath(sys.prefix)
        package_path = os.path.join(expected_prefix, 'lib', 'python2.5',
                                    'site-packages', 'myapp')
        mod = types.ModuleType('myapp')
        mod.__path__ = [package_path]
        mod.__file__ = os.path.join(package_path, '__init__.py')
        sys.modules['myapp'] = mod
        try:
            mod.app = flask.Flask(mod.__name__)
            self.assert_equal(mod.app.instance_path,
                             os.path.join(expected_prefix, 'var',
                                          'myapp-instance'))
        finally:
            sys.modules['myapp'] = None

    def test_egg_installed_paths(self):
        import types
        expected_prefix = os.path.abspath(sys.prefix)
        package_path = os.path.join(expected_prefix, 'lib', 'python2.5',
                                    'site-packages', 'MyApp.egg', 'myapp')
        mod = types.ModuleType('myapp')
        mod.__path__ = [package_path]
        mod.__file__ = os.path.join(package_path, '__init__.py')
        sys.modules['myapp'] = mod
        try:
            mod.app = flask.Flask(mod.__name__)
            self.assert_equal(mod.app.instance_path,
                             os.path.join(expected_prefix, 'var',
                                          'myapp-instance'))
        finally:
            sys.modules['myapp'] = None


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ConfigTestCase))
    suite.addTest(unittest.makeSuite(InstanceTestCase))
    return suite
