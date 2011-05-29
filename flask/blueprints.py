# -*- coding: utf-8 -*-
"""
    flask.blueprints
    ~~~~~~~~~~~~~~~~

    Blueprints are the recommended way to implement larger or more
    pluggable applications in Flask 0.7 and later.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import os

from .helpers import _PackageBoundObject, _endpoint_from_view_func


class BlueprintSetupState(object):
    """Temporary holder object for registering a blueprint with the
    application.
    """

    def __init__(self, blueprint, app, options):
        self.app = app
        self.blueprint = blueprint
        self.options = options

        subdomain = self.options.get('subdomain')
        if subdomain is None:
            subdomain = self.blueprint.subdomain
        self.subdomain = subdomain

        url_prefix = self.options.get('url_prefix')
        if url_prefix is None:
            url_prefix = self.blueprint.url_prefix
        self.url_prefix = url_prefix

    def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
        if self.url_prefix:
            rule = self.url_prefix + rule
        options.setdefault('subdomain', self.subdomain)
        if endpoint is None:
            endpoint = _endpoint_from_view_func(view_func)
        self.app.add_url_rule(rule, '%s.%s' % (self.blueprint.name, endpoint),
                              view_func, **options)


class Blueprint(_PackageBoundObject):
    """Represents a blueprint.

    .. versionadded:: 0.7
    """

    def __init__(self, name, import_name, static_folder=None,
                 static_url_path=None, url_prefix=None,
                 subdomain=None):
        _PackageBoundObject.__init__(self, import_name)
        self.name = name
        self.url_prefix = url_prefix
        self.subdomain = subdomain
        self.static_folder = static_folder
        self.static_url_path = static_url_path
        self.deferred_functions = []

    def _record(self, func):
        self.deferred_functions.append(func)

    def make_setup_state(self, app, options):
        return BlueprintSetupState(self, app, options)

    def register(self, app, options):
        """Called by :meth:`Flask.register_blueprint` to register a blueprint
        on the application.  This can be overridden to customize the register
        behavior.  Keyword arguments from
        :func:`~flask.Flask.register_blueprint` are directly forwarded to this
        method in the `options` dictionary.
        """
        state = self.make_setup_state(app, options)
        if self.has_static_folder:
            state.add_url_rule(self.static_url_path + '/<path:filename>',
                               view_func=self.send_static_file,
                               endpoint='static')

        for deferred in self.deferred_functions:
            deferred(state)

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
        """
        def register_rule(state):
            state.add_url_rule(rule, endpoint, view_func, **options)
        self._record(register_rule)

    def endpoint(self, endpoint):
        """Like :meth:`Flask.endpoint` but for a module.  This does not
        prefix the endpoint with the module name, this has to be done
        explicitly by the user of this method.
        """
        def decorator(f):
            def register_endpoint(state):
                state.app.view_functions[endpoint] = f
            self._record(register_endpoint)
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
        """
        def decorator(f):
            self._record(lambda s: s.app.errorhandler(code)(f))
            return f
        return decorator
