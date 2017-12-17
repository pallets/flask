# -*- coding: utf-8 -*-
"""
    Flaskr conftest
    ~~~~~~~~~~~~

    Defines fixtures for the Flaskr test suite.

    :copyright: (c) 2015 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import os
import tempfile
import pytest
from flaskr.factory import create_app
from flaskr.blueprints.flaskr import init_db


@pytest.fixture
def app(request):

    db_fd, temp_db_location = tempfile.mkstemp()
    config = {
        'DATABASE': temp_db_location,
        'TESTING': True,
        'DB_FD': db_fd
    }

    app = create_app(config=config)

    with app.app_context():
        init_db()
        yield app


@pytest.fixture
def client(request, app):

    client = app.test_client()

    def teardown():
        os.close(app.config['DB_FD'])
        os.unlink(app.config['DATABASE'])
    request.addfinalizer(teardown)

    return client


