import json
import os
import textwrap
from datetime import timedelta

import pytest

import flask


# config keys used for the TestConfig
TEST_KEY = "foo"
SECRET_KEY = "config"


def common_object_test(app):
    assert app.secret_key == "config"
    assert app.config["TEST_KEY"] == "foo"
    assert "TestConfig" not in app.config


def test_config_from_pyfile():
    app = flask.Flask(__name__)
    app.config.from_pyfile(f"{__file__.rsplit('.', 1)[0]}.py")
    common_object_test(app)


def test_config_from_object():
    app = flask.Flask(__name__)
    app.config.from_object(__name__)
    common_object_test(app)


def test_config_from_file():
    app = flask.Flask(__name__)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app.config.from_file(os.path.join(current_dir, "static", "config.json"), json.load)
    common_object_test(app)


def test_from_prefixed_env(monkeypatch):
    monkeypatch.setenv("FLASK_STRING", "value")
    monkeypatch.setenv("FLASK_BOOL", "true")
    monkeypatch.setenv("FLASK_INT", "1")
    monkeypatch.setenv("FLASK_FLOAT", "1.2")
    monkeypatch.setenv("FLASK_LIST", "[1, 2]")
    monkeypatch.setenv("FLASK_DICT", '{"k": "v"}')
    monkeypatch.setenv("NOT_FLASK_OTHER", "other")

    app = flask.Flask(__name__)
    app.config.from_prefixed_env()

    assert app.config["STRING"] == "value"
    assert app.config["BOOL"] is True
    assert app.config["INT"] == 1
    assert app.config["FLOAT"] == 1.2
    assert app.config["LIST"] == [1, 2]
    assert app.config["DICT"] == {"k": "v"}
    assert "OTHER" not in app.config


def test_from_prefixed_env_custom_prefix(monkeypatch):
    monkeypatch.setenv("FLASK_A", "a")
    monkeypatch.setenv("NOT_FLASK_A", "b")

    app = flask.Flask(__name__)
    app.config.from_prefixed_env("NOT_FLASK")

    assert app.config["A"] == "b"


def test_from_prefixed_env_nested(monkeypatch):
    monkeypatch.setenv("FLASK_EXIST__ok", "other")
    monkeypatch.setenv("FLASK_EXIST__inner__ik", "2")
    monkeypatch.setenv("FLASK_EXIST__new__more", '{"k": false}')
    monkeypatch.setenv("FLASK_NEW__K", "v")

    app = flask.Flask(__name__)
    app.config["EXIST"] = {"ok": "value", "flag": True, "inner": {"ik": 1}}
    app.config.from_prefixed_env()

    if os.name != "nt":
        assert app.config["EXIST"] == {
            "ok": "other",
            "flag": True,
            "inner": {"ik": 2},
            "new": {"more": {"k": False}},
        }
    else:
        # Windows env var keys are always uppercase.
        assert app.config["EXIST"] == {
            "ok": "value",
            "OK": "other",
            "flag": True,
            "inner": {"ik": 1},
            "INNER": {"IK": 2},
            "NEW": {"MORE": {"k": False}},
        }

    assert app.config["NEW"] == {"K": "v"}


def test_config_from_mapping():
    app = flask.Flask(__name__)
    app.config.from_mapping({"SECRET_KEY": "config", "TEST_KEY": "foo"})
    common_object_test(app)

    app = flask.Flask(__name__)
    app.config.from_mapping([("SECRET_KEY", "config"), ("TEST_KEY", "foo")])
    common_object_test(app)

    app = flask.Flask(__name__)
    app.config.from_mapping(SECRET_KEY="config", TEST_KEY="foo")
    common_object_test(app)

    app = flask.Flask(__name__)
    app.config.from_mapping(SECRET_KEY="config", TEST_KEY="foo", skip_key="skip")
    common_object_test(app)

    app = flask.Flask(__name__)
    with pytest.raises(TypeError):
        app.config.from_mapping({}, {})


def test_config_from_class():
    class Base:
        TEST_KEY = "foo"

    class Test(Base):
        SECRET_KEY = "config"

    app = flask.Flask(__name__)
    app.config.from_object(Test)
    common_object_test(app)


def test_config_from_envvar(monkeypatch):
    monkeypatch.setattr("os.environ", {})
    app = flask.Flask(__name__)

    with pytest.raises(RuntimeError) as e:
        app.config.from_envvar("FOO_SETTINGS")

    assert "'FOO_SETTINGS' is not set" in str(e.value)
    assert not app.config.from_envvar("FOO_SETTINGS", silent=True)

    monkeypatch.setattr(
        "os.environ", {"FOO_SETTINGS": f"{__file__.rsplit('.', 1)[0]}.py"}
    )
    assert app.config.from_envvar("FOO_SETTINGS")
    common_object_test(app)


def test_config_from_envvar_missing(monkeypatch):
    monkeypatch.setattr("os.environ", {"FOO_SETTINGS": "missing.cfg"})
    app = flask.Flask(__name__)
    with pytest.raises(IOError) as e:
        app.config.from_envvar("FOO_SETTINGS")
    msg = str(e.value)
    assert msg.startswith(
        "[Errno 2] Unable to load configuration file (No such file or directory):"
    )
    assert msg.endswith("missing.cfg'")
    assert not app.config.from_envvar("FOO_SETTINGS", silent=True)


def test_config_missing():
    app = flask.Flask(__name__)
    with pytest.raises(IOError) as e:
        app.config.from_pyfile("missing.cfg")
    msg = str(e.value)
    assert msg.startswith(
        "[Errno 2] Unable to load configuration file (No such file or directory):"
    )
    assert msg.endswith("missing.cfg'")
    assert not app.config.from_pyfile("missing.cfg", silent=True)


def test_config_missing_file():
    app = flask.Flask(__name__)
    with pytest.raises(IOError) as e:
        app.config.from_file("missing.json", load=json.load)
    msg = str(e.value)
    assert msg.startswith(
        "[Errno 2] Unable to load configuration file (No such file or directory):"
    )
    assert msg.endswith("missing.json'")
    assert not app.config.from_file("missing.json", load=json.load, silent=True)


def test_custom_config_class():
    class Config(flask.Config):
        pass

    class Flask(flask.Flask):
        config_class = Config

    app = Flask(__name__)
    assert isinstance(app.config, Config)
    app.config.from_object(__name__)
    common_object_test(app)


def test_session_lifetime():
    app = flask.Flask(__name__)
    app.config["PERMANENT_SESSION_LIFETIME"] = 42
    assert app.permanent_session_lifetime.seconds == 42


def test_send_file_max_age():
    app = flask.Flask(__name__)
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 3600
    assert app.send_file_max_age_default.seconds == 3600
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = timedelta(hours=2)
    assert app.send_file_max_age_default.seconds == 7200


def test_get_namespace():
    app = flask.Flask(__name__)
    app.config["FOO_OPTION_1"] = "foo option 1"
    app.config["FOO_OPTION_2"] = "foo option 2"
    app.config["BAR_STUFF_1"] = "bar stuff 1"
    app.config["BAR_STUFF_2"] = "bar stuff 2"
    foo_options = app.config.get_namespace("FOO_")
    assert 2 == len(foo_options)
    assert "foo option 1" == foo_options["option_1"]
    assert "foo option 2" == foo_options["option_2"]
    bar_options = app.config.get_namespace("BAR_", lowercase=False)
    assert 2 == len(bar_options)
    assert "bar stuff 1" == bar_options["STUFF_1"]
    assert "bar stuff 2" == bar_options["STUFF_2"]
    foo_options = app.config.get_namespace("FOO_", trim_namespace=False)
    assert 2 == len(foo_options)
    assert "foo option 1" == foo_options["foo_option_1"]
    assert "foo option 2" == foo_options["foo_option_2"]
    bar_options = app.config.get_namespace(
        "BAR_", lowercase=False, trim_namespace=False
    )
    assert 2 == len(bar_options)
    assert "bar stuff 1" == bar_options["BAR_STUFF_1"]
    assert "bar stuff 2" == bar_options["BAR_STUFF_2"]


@pytest.mark.parametrize("encoding", ["utf-8", "iso-8859-15", "latin-1"])
def test_from_pyfile_weird_encoding(tmpdir, encoding):
    f = tmpdir.join("my_config.py")
    f.write_binary(
        textwrap.dedent(
            f"""
            # -*- coding: {encoding} -*-
            TEST_VALUE = "föö"
            """
        ).encode(encoding)
    )
    app = flask.Flask(__name__)
    app.config.from_pyfile(str(f))
    value = app.config["TEST_VALUE"]
    assert value == "föö"
