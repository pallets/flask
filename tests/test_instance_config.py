import os

import pytest

import flask


def test_explicit_instance_paths(modules_tmp_path):
    with pytest.raises(ValueError, match=".*must be absolute"):
        flask.Flask(__name__, instance_path="instance")

    app = flask.Flask(__name__, instance_path=os.fspath(modules_tmp_path))
    assert app.instance_path == os.fspath(modules_tmp_path)


def test_uninstalled_module_paths(modules_tmp_path, purge_module):
    (modules_tmp_path / "config_module_app.py").write_text(
        "import os\n"
        "import flask\n"
        "here = os.path.abspath(os.path.dirname(__file__))\n"
        "app = flask.Flask(__name__)\n"
    )
    purge_module("config_module_app")

    from config_module_app import app

    assert app.instance_path == os.fspath(modules_tmp_path / "instance")


def test_uninstalled_package_paths(modules_tmp_path, purge_module):
    app = modules_tmp_path / "config_package_app"
    app.mkdir()
    (app / "__init__.py").write_text(
        "import os\n"
        "import flask\n"
        "here = os.path.abspath(os.path.dirname(__file__))\n"
        "app = flask.Flask(__name__)\n"
    )
    purge_module("config_package_app")

    from config_package_app import app

    assert app.instance_path == os.fspath(modules_tmp_path / "instance")


def test_uninstalled_namespace_paths(tmp_path, monkeypatch, purge_module):
    def create_namespace(package):
        project = tmp_path / f"project-{package}"
        monkeypatch.syspath_prepend(os.fspath(project))
        ns = project / "namespace" / package
        ns.mkdir(parents=True)
        (ns / "__init__.py").write_text("import flask\napp = flask.Flask(__name__)\n")
        return project

    _ = create_namespace("package1")
    project2 = create_namespace("package2")
    purge_module("namespace.package2")
    purge_module("namespace")

    from namespace.package2 import app

    assert app.instance_path == os.fspath(project2 / "instance")


def test_installed_module_paths(
    modules_tmp_path, modules_tmp_path_prefix, purge_module, site_packages, limit_loader
):
    (site_packages / "site_app.py").write_text(
        "import flask\napp = flask.Flask(__name__)\n"
    )
    purge_module("site_app")

    from site_app import app

    assert app.instance_path == os.fspath(
        modules_tmp_path / "var" / "site_app-instance"
    )


def test_installed_package_paths(
    limit_loader, modules_tmp_path, modules_tmp_path_prefix, purge_module, monkeypatch
):
    installed_path = modules_tmp_path / "path"
    installed_path.mkdir()
    monkeypatch.syspath_prepend(installed_path)

    app = installed_path / "installed_package"
    app.mkdir()
    (app / "__init__.py").write_text("import flask\napp = flask.Flask(__name__)\n")
    purge_module("installed_package")

    from installed_package import app

    assert app.instance_path == os.fspath(
        modules_tmp_path / "var" / "installed_package-instance"
    )


def test_prefix_package_paths(
    limit_loader, modules_tmp_path, modules_tmp_path_prefix, purge_module, site_packages
):
    app = site_packages / "site_package"
    app.mkdir()
    (app / "__init__.py").write_text("import flask\napp = flask.Flask(__name__)\n")
    purge_module("site_package")

    import site_package

    assert site_package.app.instance_path == os.fspath(
        modules_tmp_path / "var" / "site_package-instance"
    )
