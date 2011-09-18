# -*- coding: utf-8 -*-
"""
    flask.module
    ~~~~~~~~~~~~

    Implements a class that represents module blueprints.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import os

from .blueprints import Blueprint


def blueprint_is_module(bp):
    """Checks whether object is actually a module"""
    return isinstance(bp, Module)


class Module(Blueprint):
    """Deprecated module.

    Modules functionality has been deprecated in favor of Blueprints.

    Before Flask 0.7, the concept of Modules was basically the same as
    of Blueprints, but their functionality due to some bad semantics
    for templates and static files, has been therefore superseded by
    Blueprints.

    .. versionchanged:: 0.7
       Module has been deprecated in favor of Blueprints.
    """

    def __init__(self, import_name, name=None, url_prefix=None,
                 static_path=None, subdomain=None):
        if name is None:
            assert '.' in import_name, 'name required if package name ' \
                'does not point to a submodule'
            name = import_name.rsplit('.', 1)[1]
        Blueprint.__init__(self, name, import_name, url_prefix=url_prefix,
                           subdomain=subdomain, template_folder='templates')

        if os.path.isdir(os.path.join(self.root_path, 'static')):
            self._static_folder = 'static'
