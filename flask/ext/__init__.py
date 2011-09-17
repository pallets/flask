# -*- coding: utf-8 -*-
"""
    flask.ext
    ~~~~~~~~~

    Redirect imports for extensions.  This module basically makes it possible
    for us to transition from flaskext.foo to flask_foo without having to
    force all extensions to upgrade at the same time.

    When a user does ``from flask.ext.foo import bar`` it will attempt to
    imprt ``from flask_foo import bar`` first and when that fails it will
    try to import ``from flaskext.foo import bar``.

    We're switching from namespace packages because it was just too painful for
    everybody involved.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import sys


class _ExtensionImporter(object):
    """This importer redirects imports from this submodule to other
    locations.  This makes it possible to transition from the old
    flaskext.name to the newer flask_name without people having a
    hard time.
    """
    _module_choices = ['flask_%s', 'flaskext.%s']
    _modules = sys.modules

    def find_module(self, fullname, path=None):
        if fullname.rsplit('.', 1)[0] == __name__:
            return self

    def load_module(self, fullname):
        if fullname in self._modules:
            return self._modules[fullname]
        packname, modname = fullname.rsplit('.', 1)
        for path in self._module_choices:
            realname = path % modname
            try:
                __import__(realname)
            except ImportError:
                continue
            module = self._modules[fullname] = self._modules[realname]
            setattr(self._modules[__name__], modname, module)
            module.__loader__ = self
            return module
        raise ImportError(fullname)


sys.meta_path.append(_ExtensionImporter())
del sys, _ExtensionImporter
