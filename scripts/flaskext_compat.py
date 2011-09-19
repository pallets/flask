# -*- coding: utf-8 -*-
"""
    flaskext_compat
    ~~~~~~~~~~~~~~~

    Implements the ``flask.ext`` virtual package for versions of Flask
    older than 0.7.  This module is a noop if Flask 0.8 was detected.

    Usage::

        import flaskext_compat
        from flask.ext import foo

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import sys
import imp


ext_module = imp.new_module('flask.ext')
ext_module.__path__ = []
ext_module.__package__ = ext_module.__name__


class _ExtensionImporter(object):
    """This importer redirects imports from the flask.ext module to other
    locations.
    """
    _module_choices = ['flask_%s', 'flaskext.%s']
    prefix = ext_module.__name__ + '.'
    prefix_cutoff = prefix.count('.')

    def find_module(self, fullname, path=None):
        if fullname.startswith(self.prefix):
            return self

    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]
        modname = fullname.split('.', self.prefix_cutoff)[self.prefix_cutoff]
        for path in self._module_choices:
            realname = path % modname
            try:
                __import__(realname)
            except ImportError:
                continue
            module = sys.modules[fullname] = sys.modules[realname]
            if '.' not in modname:
                setattr(ext_module, modname, module)
            return module
        raise ImportError(fullname)


def activate():
    """Activates the compatibility system."""
    import flask
    if hasattr(flask, 'ext'):
        return
    sys.modules['flask.ext'] = flask.ext = ext_module
    sys.meta_path.append(_ExtensionImporter())
