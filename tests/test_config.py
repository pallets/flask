# -*- coding: utf-8 -*-
"""
    tests.config
    ~~~~~~~~~~~~~~~~~~~~~~

    Configuration and instances.

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import pytest

import os
import sys
import flask
import pkgutil
import unittest
import textwrap
from contextlib import contextmanager
from tests import TestFlask
from flask._compat import PY2


# config keys used for the TestConfig
TEST_KEY = 'foo'
SECRET_KEY = 'devkey'


class TestConfig(TestFlask):

    def common_object_test(self, app):
        self.assert_equal(app.secret_key, 'devkey')
        self.assert_equal(app.config['TEST_KEY'], 'foo')
        self.assert_not_in('TestConfig', app.config)

    def test_config_from_file(self):
        app = flask.Flask(__name__)
        app.config.from_pyfile(__file__.rsplit('.', 1)[0] + '.py')
        self.common_object_test(app)

    def test_config_from_object(self):
        app = flask.Flask(__name__)
        app.config.from_object(__name__)
        self.common_object_test(app)

    def test_config_from_json(self):
        app = flask.Flask(__name__)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        app.config.from_json(os.path.join(current_dir, 'static', 'config.json'))
        self.common_object_test(app)

    def test_config_from_mapping(self):
        app = flask.Flask(__name__)
        app.config.from_mapping({
            'SECRET_KEY': 'devkey',
            'TEST_KEY': 'foo'
        })
        self.common_object_test(app)

        app = flask.Flask(__name__)
        app.config.from_mapping([
            ('SECRET_KEY', 'devkey'),
            ('TEST_KEY', 'foo')
        ])
        self.common_object_test(app)

        app = flask.Flask(__name__)
        app.config.from_mapping(
            SECRET_KEY='devkey',
            TEST_KEY='foo'
        )
        self.common_object_test(app)

        app = flask.Flask(__name__)
        with self.assert_raises(TypeError):
            app.config.from_mapping(
                {}, {}
            )

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
            self.assert_false(app.config.from_envvar('FOO_SETTINGS', silent=True))
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

    def test_config_missing_json(self):
        app = flask.Flask(__name__)
        try:
            app.config.from_json('missing.json')
        except IOError as e:
            msg = str(e)
            self.assert_true(msg.startswith('[Errno 2] Unable to load configuration '
                                            'file (No such file or directory):'))
            self.assert_true(msg.endswith("missing.json'"))
        else:
            self.assert_true(0, 'expected config')
        self.assert_false(app.config.from_json('missing.json', silent=True))

    def test_custom_config_class(self):
        class Config(flask.Config):
            pass
        class Flask(flask.Flask):
            config_class = Config
        app = Flask(__name__)
        self.assert_isinstance(app.config, Config)
        app.config.from_object(__name__)
        self.common_object_test(app)

    def test_session_lifetime(self):
        app = flask.Flask(__name__)
        app.config['PERMANENT_SESSION_LIFETIME'] = 42
        self.assert_equal(app.permanent_session_lifetime.seconds, 42)

    def test_get_namespace(self):
        app = flask.Flask(__name__)
        app.config['FOO_OPTION_1'] = 'foo option 1'
        app.config['FOO_OPTION_2'] = 'foo option 2'
        app.config['BAR_STUFF_1'] = 'bar stuff 1'
        app.config['BAR_STUFF_2'] = 'bar stuff 2'
        foo_options = app.config.get_namespace('FOO_')
        self.assert_equal(2, len(foo_options))
        self.assert_equal('foo option 1', foo_options['option_1'])
        self.assert_equal('foo option 2', foo_options['option_2'])
        bar_options = app.config.get_namespace('BAR_', lowercase=False)
        self.assert_equal(2, len(bar_options))
        self.assert_equal('bar stuff 1', bar_options['STUFF_1'])
        self.assert_equal('bar stuff 2', bar_options['STUFF_2'])


@pytest.fixture(params=(True, False))
def limit_loader(request, monkeypatch):
    """Patch pkgutil.get_loader to give loader without get_filename or archive.

    This provides for tests where a system has custom loaders, e.g. Google App
    Engine's HardenedModulesHook, which have neither the `get_filename` method
    nor the `archive` attribute.

    This fixture will run the testcase twice, once with and once without the
    limitation/mock.
    """
    if not request.param:
        return

    class LimitedLoader(object):
        def __init__(self, loader):
            self.loader = loader

        def __getattr__(self, name):
            if name in ('archive', 'get_filename'):
                msg = 'Mocking a loader which does not have `%s.`' % name
                raise AttributeError(msg)
            return getattr(self.loader, name)

    old_get_loader = pkgutil.get_loader
    def get_loader(*args, **kwargs):
        return LimitedLoader(old_get_loader(*args, **kwargs))
    monkeypatch.setattr(pkgutil, 'get_loader', get_loader)

class TestInstance(TestFlask):
    @pytest.fixture
    def apps_tmpdir(self, tmpdir, monkeypatch):
        '''Test folder for all instance tests.'''
        rv = tmpdir.mkdir('test_apps')
        monkeypatch.syspath_prepend(str(rv))
        return rv

    @pytest.fixture
    def apps_tmpdir_prefix(self, apps_tmpdir, monkeypatch):
        monkeypatch.setattr(sys, 'prefix', str(apps_tmpdir))
        return apps_tmpdir

    @pytest.fixture
    def site_packages(self, apps_tmpdir, monkeypatch):
        '''Create a fake site-packages'''
        rv = apps_tmpdir \
            .mkdir('lib')\
            .mkdir('python{x[0]}.{x[1]}'.format(x=sys.version_info))\
            .mkdir('site-packages')
        monkeypatch.syspath_prepend(str(rv))
        return rv

    @pytest.fixture
    def install_egg(self, apps_tmpdir, monkeypatch):
        '''Generate egg from package name inside base and put the egg into
        sys.path'''
        def inner(name, base=apps_tmpdir):
            if not isinstance(name, str):
                raise ValueError(name)
            base.join(name).ensure_dir()
            base.join(name).join('__init__.py').ensure()

            egg_setup = base.join('setup.py')
            egg_setup.write(textwrap.dedent("""
            from setuptools import setup
            setup(name='{0}',
                  version='1.0',
                  packages=['site_egg'],
                  zip_safe=True)
            """.format(name)))

            import subprocess
            subprocess.check_call(
                [sys.executable, 'setup.py', 'bdist_egg'],
                cwd=str(apps_tmpdir)
            )
            egg_path, = apps_tmpdir.join('dist/').listdir()
            monkeypatch.syspath_prepend(str(egg_path))
            return egg_path
        return inner

    @pytest.fixture
    def purge_module(self, request):
        def inner(name):
            request.addfinalizer(lambda: sys.modules.pop(name, None))
        return inner

    def test_explicit_instance_paths(self, apps_tmpdir):
        with pytest.raises(ValueError) as excinfo:
            flask.Flask(__name__, instance_path='instance')
        assert 'must be absolute' in str(excinfo.value)

        app = flask.Flask(__name__, instance_path=str(apps_tmpdir))
        self.assert_equal(app.instance_path, str(apps_tmpdir))

    def test_main_module_paths(self, apps_tmpdir, purge_module):
        app = apps_tmpdir.join('main_app.py')
        app.write('import flask\n\napp = flask.Flask("__main__")')
        purge_module('main_app')

        from main_app import app
        here = os.path.abspath(os.getcwd())
        assert app.instance_path == os.path.join(here, 'instance')

    def test_uninstalled_module_paths(self, apps_tmpdir, purge_module):
        app = apps_tmpdir.join('config_module_app.py').write(
            'import os\n'
            'import flask\n'
            'here = os.path.abspath(os.path.dirname(__file__))\n'
            'app = flask.Flask(__name__)\n'
        )
        purge_module('config_module_app')

        from config_module_app import app
        assert app.instance_path == str(apps_tmpdir.join('instance'))

    def test_uninstalled_package_paths(self, apps_tmpdir, purge_module):
        app = apps_tmpdir.mkdir('config_package_app')
        init = app.join('__init__.py')
        init.write(
            'import os\n'
            'import flask\n'
            'here = os.path.abspath(os.path.dirname(__file__))\n'
            'app = flask.Flask(__name__)\n'
        )
        purge_module('config_package_app')

        from config_package_app import app
        assert app.instance_path == str(apps_tmpdir.join('instance'))

    def test_installed_module_paths(self, apps_tmpdir, apps_tmpdir_prefix,
                                    purge_module, site_packages, limit_loader):
        site_packages.join('site_app.py').write(
            'import flask\n'
            'app = flask.Flask(__name__)\n'
        )
        purge_module('site_app')

        from site_app import app
        assert app.instance_path == \
            apps_tmpdir.join('var').join('site_app-instance')

    def test_installed_package_paths(self, limit_loader, apps_tmpdir,
                                     apps_tmpdir_prefix, purge_module,
                                     monkeypatch):
        installed_path = apps_tmpdir.mkdir('path')
        monkeypatch.syspath_prepend(installed_path)

        app = installed_path.mkdir('installed_package')
        init = app.join('__init__.py')
        init.write('import flask\napp = flask.Flask(__name__)')
        purge_module('installed_package')

        from installed_package import app
        assert app.instance_path == \
            apps_tmpdir.join('var').join('installed_package-instance')

    def test_prefix_package_paths(self, limit_loader, apps_tmpdir,
                                  apps_tmpdir_prefix, purge_module,
                                  site_packages):
        app = site_packages.mkdir('site_package')
        init = app.join('__init__.py')
        init.write('import flask\napp = flask.Flask(__name__)')
        purge_module('site_package')

        import site_package
        assert site_package.app.instance_path == \
            apps_tmpdir.join('var').join('site_package-instance')

    def test_egg_installed_paths(self, install_egg, apps_tmpdir,
                                 apps_tmpdir_prefix):
        apps_tmpdir.mkdir('site_egg').join('__init__.py').write(
            'import flask\n\napp = flask.Flask(__name__)'
        )
        install_egg('site_egg')
        try:
            import site_egg
            assert site_egg.app.instance_path == \
                str(apps_tmpdir.join('var/').join('site_egg-instance'))
        finally:
            if 'site_egg' in sys.modules:
                del sys.modules['site_egg']

    if PY2:
        def test_meta_path_loader_without_is_package(self):
            class Loader(object):
                def find_module(self, name):
                    return self
            sys.meta_path.append(Loader())
            try:
                with self.assert_raises(AttributeError):
                    flask.Flask(__name__)
            finally:
                sys.meta_path.pop()
