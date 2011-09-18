# -*- coding: utf-8 -*-
"""
    flask.ext
    ~~~~~~~~~

    Redirector for extension imports. This module makes it possible to
    transition from the old namespaced packages (``flaskext.foo``) to
    the new ``flask_foo`` packages without having to force upgrades
    (and creating breakages) for all the extensions at the same time.

    When user does ``from flask.ext.foo import bar`` module attempts to
    do ``from flask_foo import bar`` first and if this fails,
    ``from flaskext.foo import bar`` is run instead.

    We're switching from namespace packages because it was just too painful for
    everybody involved.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""


class _ExtensionImporter(object):
    """This importer redirects imports from this submodule to other locations,
    making it possible to transition from the old flaskext.name to the
    newer flask_name without giving people a hard time.
    """
    _module_choices = ['flask_%s', 'flaskext.%s']

    def __init__(self):
        from sys import meta_path
        self.prefix = __name__ + '.'
        self.prefix_cutoff = __name__.count('.') + 1

        # since people might reload the flask.ext module (by accident or
        # intentionally) we have to make sure to not add more than one
        # import hook.  We can't check class types here either since a new
        # class will be created on reload.  As a result of that we check
        # the name of the class and remove stale instances.
        def _name(x):
            cls = type(x)
            return cls.__module__ + '.' + cls.__name__
        this = _name(self)
        meta_path[:] = [x for x in meta_path if _name(x) != this] + [self]

    def find_module(self, fullname, path=None):
        if fullname.startswith(self.prefix):
            return self

    def load_module(self, fullname):
        from sys import modules
        if fullname in modules:
            return modules[fullname]
        modname = fullname.split('.', self.prefix_cutoff)[self.prefix_cutoff]
        for path in self._module_choices:
            realname = path % modname
            try:
                __import__(realname)
            except ImportError:
                continue
            module = modules[fullname] = modules[realname]
            if '.' not in modname:
                setattr(modules[__name__], modname, module)
            return module
        raise ImportError(fullname)


_ExtensionImporter()
del _ExtensionImporter
