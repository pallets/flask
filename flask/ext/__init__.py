# -*- coding: utf-8 -*-
"""
    flask.ext
    ~~~~~~~~~

    Redirect imports for extensions.  This module basically makes it possible
    for us to transition from flaskext.foo to flask_foo without having to
    force all extensions to upgrade at the same time.

    When a user does ``from flask.ext.foo import bar`` it will attempt to
    import ``from flask_foo import bar`` first and when that fails it will
    try to import ``from flaskext.foo import bar``.

    We're switching from namespace packages because it was just too painful for
    everybody involved.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""


class _ExtensionImporter(object):
    """This importer redirects imports from this submodule to other locations.
    This makes it possible to transition from the old flaskext.name to the
    newer flask_name without people having a hard time.
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
        from sys import modules, exc_info
        if fullname in modules:
            return modules[fullname]
        modname = fullname.split('.', self.prefix_cutoff)[self.prefix_cutoff]
        for path in self._module_choices:
            realname = path % modname
            try:
                __import__(realname)
            except ImportError:
                exc_type, exc_value, tb = exc_info()
                # since we only establish the entry in sys.modules at the
                # very this seems to be redundant, but if recursive imports
                # happen we will call into the move import a second time.
                # On the second invocation we still don't have an entry for
                # fullname in sys.modules, but we will end up with the same
                # fake module name and that import will succeed since this
                # one already has a temporary entry in the modules dict.
                # Since this one "succeeded" temporarily that second
                # invocation now will have created a fullname entry in
                # sys.modules which we have to kill.
                modules.pop(fullname, None)
                if self.is_important_traceback(realname, tb):
                    raise exc_type, exc_value, tb
                continue
            module = modules[fullname] = modules[realname]
            if '.' not in modname:
                setattr(modules[__name__], modname, module)
            return module
        raise ImportError('No module named %s' % fullname)

    def is_important_traceback(self, important_module, tb):
        """Walks a traceback's frames and checks if any of the frames
        originated in the given important module.  If that is the case
        then we were able to import the module itself but apparently
        something went wrong when the module was imported.  (Eg: import
        of an import failed).
        """
        # Why can we access f_globals' __name__ here and the value is
        # not None?  I honestly don't know but here is my thinking.
        # The module owns a reference to globals and the frame has one.
        # Each function only keeps a reference to the globals not do the
        # module which normally causes the problem that when the module
        # shuts down all globals are set to None.  Now however when the
        # import system fails Python takes the short way out and does not
        # actually properly shut down the module by Noneing the values
        # but by just removing the entry from sys.modules.  This means
        # that the regular reference based cleanup kicks in.
        #
        # The good thing: At worst we will swallow an exception we should
        # not and the error message will be messed up.  However I think
        # this should be sufficiently reliable.
        while tb is not None:
            if tb.tb_frame.f_globals.get('__name__') == important_module:
                return True
            tb = tb.tb_next
        return False


_ExtensionImporter()
del _ExtensionImporter
