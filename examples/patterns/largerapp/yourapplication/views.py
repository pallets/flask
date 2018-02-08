# -*- coding: utf-8 -*-
"""
yourapplication.views
~~~~~~~~~~~~~~~~~~~~~

:copyright: © 2010 by the Pallets team.
:license: BSD, see LICENSE for more details.
"""

from yourapplication import app

@app.route('/')
def index():
    return 'Hello World!'
