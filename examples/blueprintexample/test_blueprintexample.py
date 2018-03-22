# -*- coding: utf-8 -*-
"""
Blueprint Example Tests
~~~~~~~~~~~~~~~~~~~~~~~

:copyright: © 2010 by the Pallets team.
:license: BSD, see LICENSE for more details.
"""

import pytest

import blueprintexample


@pytest.fixture
def client():
    return blueprintexample.app.test_client()


def test_urls(client):
    r = client.get('/')
    assert r.status_code == 200

    r = client.get('/hello')
    assert r.status_code == 200

    r = client.get('/world')
    assert r.status_code == 200

    # second blueprint instance
    r = client.get('/pages/hello')
    assert r.status_code == 200

    r = client.get('/pages/world')
    assert r.status_code == 200
