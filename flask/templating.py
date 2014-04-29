# -*- coding: utf-8 -*-
"""
    flask.templating
    ~~~~~~~~~~~~~~~~

    Implements the bridge to Jinja2.

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import sys
import logging
import posixpath
from jinja2 import BaseLoader, Environment as BaseEnvironment, \
    TemplateNotFound, Undefined

from .globals import _request_ctx_stack, _app_ctx_stack
from .signals import template_rendered
from .module import blueprint_is_module
from ._compat import itervalues, iteritems, implements_to_string, string_types
from jinja2.utils import missing, object_type_repr


def _default_template_ctx_processor():
    """Default template context processor.  Injects `request`,
    `session` and `g`.
    """
    reqctx = _request_ctx_stack.top
    appctx = _app_ctx_stack.top
    rv = {}
    if appctx is not None:
        rv['g'] = appctx.g
    if reqctx is not None:
        rv['request'] = reqctx.request
        rv['session'] = reqctx.session
    return rv


@implements_to_string
class LoggingUndefined(Undefined):
    """
    An undefined type that logs to stdout when trying to write out the variable
    in a jinja template.
    """

    __slots__ = ()
    logger = logging.getLogger(__name__)

    def __init__(self, *args, **kwargs):
        ch = logging.StreamHandler(sys.stdout)
        self.logger.addHandler(ch)
        Undefined.__init__(self, *args, **kwargs)

    def __str__(self):
        # Takes aim from jinja2.runtime.DebugUndefined
        if self._undefined_hint is None:
            if self._undefined_obj is missing:
                hint = '{variable} is undefined'.format(
                    variable=self._undefined_name)
            elif not isinstance(self._undefined_name, string_types):
                hint = '{object} has no element {element}'.format(
                    object=object_type_repr(self._undefined_obj),
                    element=self._undefined_name)
            else:
                hint = '{object} has no attribute {attribute}'.format(
                    object=object_type_repr(self._undefined_obj),
                    attribute=self._undefined_name)
        else:
            hint = self._undefined_hint
        self.logger.error('Template error: {hint}'.format(hint=hint))
        # Return a empty string so that the variable in the template is empty
        # on render.
        return u''


class Environment(BaseEnvironment):
    """Works like a regular Jinja2 environment but has some additional
    knowledge of how Flask's blueprint works so that it can prepend the
    name of the blueprint to referenced templates if necessary.
    """

    def __init__(self, app, **options):
        if 'loader' not in options:
            options['loader'] = app.create_global_jinja_loader()
        if 'undefined' not in options:
            options['undefined'] = LoggingUndefined if app.debug else Undefined
        BaseEnvironment.__init__(self, **options)
        self.app = app


class DispatchingJinjaLoader(BaseLoader):
    """A loader that looks for templates in the application and all
    the blueprint folders.
    """

    def __init__(self, app):
        self.app = app

    def get_source(self, environment, template):
        for loader, local_name in self._iter_loaders(template):
            try:
                return loader.get_source(environment, local_name)
            except TemplateNotFound:
                pass

        raise TemplateNotFound(template)

    def _iter_loaders(self, template):
        loader = self.app.jinja_loader
        if loader is not None:
            yield loader, template

        # old style module based loaders in case we are dealing with a
        # blueprint that is an old style module
        try:
            module, local_name = posixpath.normpath(template).split('/', 1)
            blueprint = self.app.blueprints[module]
            if blueprint_is_module(blueprint):
                loader = blueprint.jinja_loader
                if loader is not None:
                    yield loader, local_name
        except (ValueError, KeyError):
            pass

        for blueprint in itervalues(self.app.blueprints):
            if blueprint_is_module(blueprint):
                continue
            loader = blueprint.jinja_loader
            if loader is not None:
                yield loader, template

    def list_templates(self):
        result = set()
        loader = self.app.jinja_loader
        if loader is not None:
            result.update(loader.list_templates())

        for name, blueprint in iteritems(self.app.blueprints):
            loader = blueprint.jinja_loader
            if loader is not None:
                for template in loader.list_templates():
                    prefix = ''
                    if blueprint_is_module(blueprint):
                        prefix = name + '/'
                    result.add(prefix + template)

        return list(result)


def _render(template, context, app):
    """Renders the template and fires the signal"""
    rv = template.render(context)
    template_rendered.send(app, template=template, context=context)
    return rv


def render_template(template_name_or_list, **context):
    """Renders a template from the template folder with the given
    context.

    :param template_name_or_list: the name of the template to be
                                  rendered, or an iterable with template names
                                  the first one existing will be rendered
    :param context: the variables that should be available in the
                    context of the template.
    """
    ctx = _app_ctx_stack.top
    ctx.app.update_template_context(context)
    return _render(
        ctx.app.jinja_env.get_or_select_template(template_name_or_list),
        context, ctx.app)


def render_template_string(source, **context):
    """Renders a template from the given template source string
    with the given context.

    :param source: the sourcecode of the template to be
                   rendered
    :param context: the variables that should be available in the
                    context of the template.
    """
    ctx = _app_ctx_stack.top
    ctx.app.update_template_context(context)
    return _render(ctx.app.jinja_env.from_string(source),
                   context, ctx.app)
