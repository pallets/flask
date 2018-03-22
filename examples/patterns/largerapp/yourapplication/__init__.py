# -*- coding: utf-8 -*-
"""
yourapplication
~~~~~~~~~~~~~~~

:copyright: © 2010 by the Pallets team.
:license: BSD, see LICENSE for more details.
"""

from flask import Flask
app = Flask('yourapplication')

import yourapplication.views
