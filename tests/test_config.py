# -*- coding: utf-8 -*-
"""
    tests.test_config
    ~~~~~~~~~~~~~~~~~

    :copyright: 2010 Pallets
    :license: BSD-3-Clause
"""

from datetime import timedelta
import os
import textwrap

import flask
from flask._compat import PY2
import pytest


# config keys used for the TestConfig
TEST_KEY = 'foo'
SECRET_KEY = 'config'


def common_object_test(app):
    assert app.secret_key == 'config'
    assert app.config['TEST_KEY'] == 'foo'
    assert 'TestConfig' not in app.config


def test_config_from_file():
    app = flask.Flask(__name__)
    app.config.from_pyfile(__file__.rsplit('.', 1)[0] + '.py')
    common_object_test(app)


def test_config_from_object():
    app = flask.Flask(__name__)
    app.config.from_object(__name__)
    common_object_test(app)


def test_config_from_json():
    app = flask.Flask(__name__)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app.config.from_json(os.path.join(current_dir, 'static', 'config.json'))
    common_object_test(app)


def test_config_from_mapping():
    app = flask.Flask(__name__)
    app.config.from_mapping({
        'SECRET_KEY': 'config',
        'TEST_KEY': 'foo'
    })
    common_object_test(app)

    app = flask.Flask(__name__)
    app.config.from_mapping([
        ('SECRET_KEY', 'config'),
        ('TEST_KEY', 'foo')
    ])
    common_object_test(app)

    app = flask.Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY='config',
        TEST_KEY='foo'
    )
    common_object_test(app)

    app = flask.Flask(__name__)
    with pytest.raises(TypeError):
        app.config.from_mapping(
            {}, {}
        )


def test_config_from_class():
    class Base(object):
        TEST_KEY = 'foo'

    class Test(Base):
        SECRET_KEY = 'config'

    app = flask.Flask(__name__)
    app.config.from_object(Test)
    common_object_test(app)


def test_config_from_envvar():
    env = os.environ
    try:
        os.environ = {}
        app = flask.Flask(__name__)
        with pytest.raises(RuntimeError) as e:
            app.config.from_envvar('FOO_SETTINGS')
        assert "'FOO_SETTINGS' is not set" in str(e.value)
        assert not app.config.from_envvar('FOO_SETTINGS', silent=True)

        os.environ = {'FOO_SETTINGS': __file__.rsplit('.', 1)[0] + '.py'}
        assert app.config.from_envvar('FOO_SETTINGS')
        common_object_test(app)
    finally:
        os.environ = env


def test_config_from_envvar_missing():
    env = os.environ
    try:
        os.environ = {'FOO_SETTINGS': 'missing.cfg'}
        with pytest.raises(IOError) as e:
            app = flask.Flask(__name__)
            app.config.from_envvar('FOO_SETTINGS')
        msg = str(e.value)
        assert msg.startswith('[Errno 2] Unable to load configuration '
                              'file (No such file or directory):')
        assert msg.endswith("missing.cfg'")
        assert not app.config.from_envvar('FOO_SETTINGS', silent=True)
    finally:
        os.environ = env


def test_config_missing():
    app = flask.Flask(__name__)
    with pytest.raises(IOError) as e:
        app.config.from_pyfile('missing.cfg')
    msg = str(e.value)
    assert msg.startswith('[Errno 2] Unable to load configuration '
                          'file (No such file or directory):')
    assert msg.endswith("missing.cfg'")
    assert not app.config.from_pyfile('missing.cfg', silent=True)


def test_config_missing_json():
    app = flask.Flask(__name__)
    with pytest.raises(IOError) as e:
        app.config.from_json('missing.json')
    msg = str(e.value)
    assert msg.startswith('[Errno 2] Unable to load configuration '
                          'file (No such file or directory):')
    assert msg.endswith("missing.json'")
    assert not app.config.from_json('missing.json', silent=True)


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
    app.config['PERMANENT_SESSION_LIFETIME'] = 42
    assert app.permanent_session_lifetime.seconds == 42


def test_send_file_max_age():
    app = flask.Flask(__name__)
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 3600
    assert app.send_file_max_age_default.seconds == 3600
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(hours=2)
    assert app.send_file_max_age_default.seconds == 7200


def test_get_namespace():
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
    foo_options = app.config.get_namespace('FOO_', trim_namespace=False)
    assert 2 == len(foo_options)
    assert 'foo option 1' == foo_options['foo_option_1']
    assert 'foo option 2' == foo_options['foo_option_2']
    bar_options = app.config.get_namespace('BAR_', lowercase=False, trim_namespace=False)
    assert 2 == len(bar_options)
    assert 'bar stuff 1' == bar_options['BAR_STUFF_1']
    assert 'bar stuff 2' == bar_options['BAR_STUFF_2']


@pytest.mark.parametrize('encoding', ['utf-8', 'iso-8859-15', 'latin-1'])
def test_from_pyfile_weird_encoding(tmpdir, encoding):
    f = tmpdir.join('my_config.py')
    f.write_binary(textwrap.dedent(u'''
    # -*- coding: {0} -*-
    TEST_VALUE = "föö"
    '''.format(encoding)).encode(encoding))
    app = flask.Flask(__name__)
    app.config.from_pyfile(str(f))
    value = app.config['TEST_VALUE']
    if PY2:
        value = value.decode(encoding)
    assert value == u'föö'
