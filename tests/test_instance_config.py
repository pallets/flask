# -*- coding: utf-8 -*-
"""
    tests.test_instance
    ~~~~~~~~~~~~~~~~~~~

    :copyright: 2010 Pallets
    :license: BSD-3-Clause
"""

import os
import sys

import pytest
import flask
from flask._compat import PY2


def test_explicit_instance_paths(modules_tmpdir):
    with pytest.raises(ValueError) as excinfo:
        flask.Flask(__name__, instance_path='instance')
    assert 'must be absolute' in str(excinfo.value)

    app = flask.Flask(__name__, instance_path=str(modules_tmpdir))
    assert app.instance_path == str(modules_tmpdir)


def test_main_module_paths(modules_tmpdir, purge_module):
    app = modules_tmpdir.join('main_app.py')
    app.write('import flask\n\napp = flask.Flask("__main__")')
    purge_module('main_app')

    from main_app import app
    here = os.path.abspath(os.getcwd())
    assert app.instance_path == os.path.join(here, 'instance')


def test_uninstalled_module_paths(modules_tmpdir, purge_module):
    app = modules_tmpdir.join('config_module_app.py').write(
        'import os\n'
        'import flask\n'
        'here = os.path.abspath(os.path.dirname(__file__))\n'
        'app = flask.Flask(__name__)\n'
    )
    purge_module('config_module_app')

    from config_module_app import app
    assert app.instance_path == str(modules_tmpdir.join('instance'))


def test_uninstalled_package_paths(modules_tmpdir, purge_module):
    app = modules_tmpdir.mkdir('config_package_app')
    init = app.join('__init__.py')
    init.write(
        'import os\n'
        'import flask\n'
        'here = os.path.abspath(os.path.dirname(__file__))\n'
        'app = flask.Flask(__name__)\n'
    )
    purge_module('config_package_app')

    from config_package_app import app
    assert app.instance_path == str(modules_tmpdir.join('instance'))


def test_installed_module_paths(modules_tmpdir, modules_tmpdir_prefix,
                                purge_module, site_packages, limit_loader):
    site_packages.join('site_app.py').write(
        'import flask\n'
        'app = flask.Flask(__name__)\n'
    )
    purge_module('site_app')

    from site_app import app
    assert app.instance_path == \
        modules_tmpdir.join('var').join('site_app-instance')


def test_installed_package_paths(limit_loader, modules_tmpdir,
                                 modules_tmpdir_prefix, purge_module,
                                 monkeypatch):
    installed_path = modules_tmpdir.mkdir('path')
    monkeypatch.syspath_prepend(installed_path)

    app = installed_path.mkdir('installed_package')
    init = app.join('__init__.py')
    init.write('import flask\napp = flask.Flask(__name__)')
    purge_module('installed_package')

    from installed_package import app
    assert app.instance_path == \
        modules_tmpdir.join('var').join('installed_package-instance')


def test_prefix_package_paths(limit_loader, modules_tmpdir,
                              modules_tmpdir_prefix, purge_module,
                              site_packages):
    app = site_packages.mkdir('site_package')
    init = app.join('__init__.py')
    init.write('import flask\napp = flask.Flask(__name__)')
    purge_module('site_package')

    import site_package
    assert site_package.app.instance_path == \
        modules_tmpdir.join('var').join('site_package-instance')


def test_egg_installed_paths(install_egg, modules_tmpdir,
                             modules_tmpdir_prefix):
    modules_tmpdir.mkdir('site_egg').join('__init__.py').write(
        'import flask\n\napp = flask.Flask(__name__)'
    )
    install_egg('site_egg')
    try:
        import site_egg
        assert site_egg.app.instance_path == \
            str(modules_tmpdir.join('var/').join('site_egg-instance'))
    finally:
        if 'site_egg' in sys.modules:
            del sys.modules['site_egg']


@pytest.mark.skipif(not PY2, reason='This only works under Python 2.')
def test_meta_path_loader_without_is_package(request, modules_tmpdir):
    app = modules_tmpdir.join('unimportable.py')
    app.write('import flask\napp = flask.Flask(__name__)')

    class Loader(object):
        def find_module(self, name, path=None):
            return self

    sys.meta_path.append(Loader())
    request.addfinalizer(sys.meta_path.pop)

    with pytest.raises(AttributeError):
        import unimportable
