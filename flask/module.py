# -*- coding: utf-8 -*-
"""
    flask.module
    ~~~~~~~~~~~~

    Implements a class that represents module blueprints.

    :copyright: (c) 2010 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from .helpers import _PackageBoundObject, _endpoint_from_view_func


def _register_module(module, static_path):
    """Internal helper function that returns a function for recording
    that registers the `send_static_file` function for the module on
    the application if necessary.  It also registers the module on
    the application.
    """
    def _register(state):
        state.app.modules[module.name] = module
        # do not register the rule if the static folder of the
        # module is the same as the one from the application.
        if state.app.root_path == module.root_path:
            return
        path = static_path
        if path is None:
            path = state.app.static_path
        if state.url_prefix:
            path = state.url_prefix + path
        state.app.add_url_rule(path + '/<path:filename>',
                               endpoint='%s.static' % module.name,
                               view_func=module.send_static_file,
                               subdomain=state.subdomain)
    return _register


class _ModuleSetupState(object):

    def __init__(self, app, url_prefix=None, subdomain=None):
        self.app = app
        self.url_prefix = url_prefix
        self.subdomain = subdomain


class Module(_PackageBoundObject):
    """Container object that enables pluggable applications.  A module can
    be used to organize larger applications.  They represent blueprints that,
    in combination with a :class:`Flask` object are used to create a large
    application.

    A module is like an application bound to an `import_name`.  Multiple
    modules can share the same import names, but in that case a `name` has
    to be provided to keep them apart.  If different import names are used,
    the rightmost part of the import name is used as name.

    Here's an example structure for a larger application::

        /myapplication
            /__init__.py
            /views
                /__init__.py
                /admin.py
                /frontend.py

    The `myapplication/__init__.py` can look like this::

        from flask import Flask
        from myapplication.views.admin import admin
        from myapplication.views.frontend import frontend

        app = Flask(__name__)
        app.register_module(admin, url_prefix='/admin')
        app.register_module(frontend)

    And here's an example view module (`myapplication/views/admin.py`)::

        from flask import Module

        admin = Module(__name__)

        @admin.route('/')
        def index():
            pass

        @admin.route('/login')
        def login():
            pass

    For a gentle introduction into modules, checkout the
    :ref:`working-with-modules` section.

    .. versionadded:: 0.5
       The `static_path` parameter was added and it's now possible for
       modules to refer to their own templates and static files.  See
       :ref:`modules-and-resources` for more information.

    .. versionadded:: 0.6
       The `subdomain` parameter was added.

    :param import_name: the name of the Python package or module
                        implementing this :class:`Module`.
    :param name: the internal short name for the module.  Unless specified
                 the rightmost part of the import name
    :param url_prefix: an optional string that is used to prefix all the
                       URL rules of this module.  This can also be specified
                       when registering the module with the application.
    :param subdomain: used to set the subdomain setting for URL rules that
                      do not have a subdomain setting set.
    :param static_path: can be used to specify a different path for the
                        static files on the web.  Defaults to ``/static``.
                        This does not affect the folder the files are served
                        *from*.
    """

    def __init__(self, import_name, name=None, url_prefix=None,
                 static_path=None, subdomain=None):
        if name is None:
            assert '.' in import_name, 'name required if package name ' \
                'does not point to a submodule'
            name = import_name.rsplit('.', 1)[1]
        _PackageBoundObject.__init__(self, import_name)
        self.name = name
        self.url_prefix = url_prefix
        self.subdomain = subdomain
        self.view_functions = {}
        self._register_events = [_register_module(self, static_path)]

    def route(self, rule, **options):
        """Like :meth:`Flask.route` but for a module.  The endpoint for the
        :func:`url_for` function is prefixed with the name of the module.
        """
        def decorator(f):
            self.add_url_rule(rule, f.__name__, f, **options)
            return f
        return decorator

    def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
        """Like :meth:`Flask.add_url_rule` but for a module.  The endpoint for
        the :func:`url_for` function is prefixed with the name of the module.

        .. versionchanged:: 0.6
           The `endpoint` argument is now optional and will default to the
           function name to consistent with the function of the same name
           on the application object.
        """
        def register_rule(state):
            the_rule = rule
            if state.url_prefix:
                the_rule = state.url_prefix + rule
            options.setdefault('subdomain', state.subdomain)
            the_endpoint = endpoint
            if the_endpoint is None:
                the_endpoint = _endpoint_from_view_func(view_func)
            state.app.add_url_rule(the_rule, '%s.%s' % (self.name,
                                                        the_endpoint),
                                   view_func, **options)
        self._record(register_rule)

    def endpoint(self, endpoint):
        """Like :meth:`Flask.endpoint` but for a module."""
        def decorator(f):
            self.view_functions[endpoint] = f
            return f
        return decorator

    def before_request(self, f):
        """Like :meth:`Flask.before_request` but for a module.  This function
        is only executed before each request that is handled by a function of
        that module.
        """
        self._record(lambda s: s.app.before_request_funcs
            .setdefault(self.name, []).append(f))
        return f

    def before_app_request(self, f):
        """Like :meth:`Flask.before_request`.  Such a function is executed
        before each request, even if outside of a module.
        """
        self._record(lambda s: s.app.before_request_funcs
            .setdefault(None, []).append(f))
        return f

    def after_request(self, f):
        """Like :meth:`Flask.after_request` but for a module.  This function
        is only executed after each request that is handled by a function of
        that module.
        """
        self._record(lambda s: s.app.after_request_funcs
            .setdefault(self.name, []).append(f))
        return f

    def after_app_request(self, f):
        """Like :meth:`Flask.after_request` but for a module.  Such a function
        is executed after each request, even if outside of the module.
        """
        self._record(lambda s: s.app.after_request_funcs
            .setdefault(None, []).append(f))
        return f

    def context_processor(self, f):
        """Like :meth:`Flask.context_processor` but for a module.  This
        function is only executed for requests handled by a module.
        """
        self._record(lambda s: s.app.template_context_processors
            .setdefault(self.name, []).append(f))
        return f

    def app_context_processor(self, f):
        """Like :meth:`Flask.context_processor` but for a module.  Such a
        function is executed each request, even if outside of the module.
        """
        self._record(lambda s: s.app.template_context_processors
            .setdefault(None, []).append(f))
        return f

    def app_errorhandler(self, code):
        """Like :meth:`Flask.errorhandler` but for a module.  This
        handler is used for all requests, even if outside of the module.

        .. versionadded:: 0.4
        """
        def decorator(f):
            self._record(lambda s: s.app.errorhandler(code)(f))
            return f
        return decorator

    def _record(self, func):
        self._register_events.append(func)
