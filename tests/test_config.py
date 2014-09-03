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

from flask._compat import PY2


# config keys used for the TestConfig
TEST_KEY = 'foo'
SECRET_KEY = 'devkey'


class TestConfig(object):

    def common_object_test(self, app):
        assert app.secret_key == 'devkey'
        assert app.config['TEST_KEY'] == 'foo'
        assert 'TestConfig' not in app.config

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
        with pytest.raises(TypeError):
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
                assert "'FOO_SETTINGS' is not set" in str(e)
            else:
                assert 0, 'expected exception'
            assert not app.config.from_envvar('FOO_SETTINGS', silent=True)

            os.environ = {'FOO_SETTINGS': __file__.rsplit('.', 1)[0] + '.py'}
            assert app.config.from_envvar('FOO_SETTINGS')
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
                assert msg.startswith('[Errno 2] Unable to load configuration '
                                      'file (No such file or directory):')
                assert msg.endswith("missing.cfg'")
            else:
                assert False, 'expected IOError'
            assert not app.config.from_envvar('FOO_SETTINGS', silent=True)
        finally:
            os.environ = env

    def test_config_missing(self):
        app = flask.Flask(__name__)
        try:
            app.config.from_pyfile('missing.cfg')
        except IOError as e:
            msg = str(e)
            assert msg.startswith('[Errno 2] Unable to load configuration '
                                  'file (No such file or directory):')
            assert msg.endswith("missing.cfg'")
        else:
            assert 0, 'expected config'
        assert not app.config.from_pyfile('missing.cfg', silent=True)

    def test_config_missing_json(self):
        app = flask.Flask(__name__)
        try:
            app.config.from_json('missing.json')
        except IOError as e:
            msg = str(e)
            assert msg.startswith('[Errno 2] Unable to load configuration '
                                  'file (No such file or directory):')
            assert msg.endswith("missing.json'")
        else:
            assert 0, 'expected config'
        assert not app.config.from_json('missing.json', silent=True)

    def test_custom_config_class(self):
        class Config(flask.Config):
            pass
        class Flask(flask.Flask):
            config_class = Config
        app = Flask(__name__)
        assert isinstance(app.config, Config)
        app.config.from_object(__name__)
        self.common_object_test(app)

    def test_session_lifetime(self):
        app = flask.Flask(__name__)
        app.config['PERMANENT_SESSION_LIFETIME'] = 42
        assert app.permanent_session_lifetime.seconds == 42

    def test_get_namespace(self):
        app = flask.Flask(__name__)
        app.config['FOO_OPTION_1'] = 'foo option 1'
        app.config['FOO_OPTION_2'] = 'foo option 2'
        app.config['BAR_STUFF_1'] = 'bar stuff 1'
        app.config['BAR_STUFF_2'] = 'bar stuff 2'
        foo_options = app.config.get_namespace('FOO_')
        assert 2 == len(foo_options)
        assert 'foo option 1' == foo_options['option_1']
        assert 'foo option 2' == foo_options['option_2']
        bar_options = app.config.get_namespace('BAR_', lowercase=False)
        assert 2 == len(bar_options)
        assert 'bar stuff 1' == bar_options['STUFF_1']
        assert 'bar stuff 2' == bar_options['STUFF_2']


class TestInstance(object):
    def test_explicit_instance_paths(self, apps_tmpdir):
        with pytest.raises(ValueError) as excinfo:
            flask.Flask(__name__, instance_path='instance')
        assert 'must be absolute' in str(excinfo.value)

        app = flask.Flask(__name__, instance_path=str(apps_tmpdir))
        assert app.instance_path == str(apps_tmpdir)

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
                with pytest.raises(AttributeError):
                    flask.Flask(__name__)
            finally:
                sys.meta_path.pop()
