# -*- coding: utf-8 -*-
"""
    flask.templating
    ~~~~~~~~~~~~~~~~

    Implements the bridge to Jinja2.

    :copyright: (c) 2010 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import posixpath
from jinja2 import BaseLoader, Environment as BaseEnvironment, \
     TemplateNotFound

from .globals import _request_ctx_stack
from .signals import template_rendered


def _default_template_ctx_processor():
    """Default template context processor.  Injects `request`,
    `session` and `g`.
    """
    reqctx = _request_ctx_stack.top
    return dict(
        config=reqctx.app.config,
        request=reqctx.request,
        session=reqctx.session,
        g=reqctx.g
    )


class Environment(BaseEnvironment):
    """Works like a regular Jinja2 environment but has some additional
    knowledge of how Flask's blueprint works so that it can prepend the
    name of the blueprint to referenced templates if necessary.
    """

    def __init__(self, app, **options):
        if 'loader' not in options:
            options['loader'] = app.create_jinja_loader()
        BaseEnvironment.__init__(self, **options)
        self.app = app

    def join_path(self, template, parent):
        if template and template[0] == ':':
            template = parent.split(':', 1)[0] + template
        return template


class DispatchingJinjaLoader(BaseLoader):
    """A loader that looks for templates in the application and all
    the module folders.
    """

    def __init__(self, app):
        self.app = app

    def get_source(self, environment, template):
        # newstyle template support.  blueprints are explicit and no further
        # magic is involved.  If the template cannot be loaded by the
        # blueprint loader it just gives up, no further steps involved.
        if ':' in template:
            blueprint_name, local_template = template.split(':', 1)
            local_template = posixpath.normpath(local_template)
            blueprint = self.app.blueprints.get(blueprint_name)
            if blueprint is None:
                raise TemplateNotFound(template)
            loader = blueprint.jinja_loader
            if loader is not None:
                return loader.get_source(environment, local_template)

        # if modules are enabled we call into the old style template lookup
        # and try that before we go with the real deal.
        loader = None
        try:
            module, name = posixpath.normpath(template).split('/', 1)
            loader = self.app.modules[module].jinja_loader
        except (ValueError, KeyError, TemplateNotFound):
            pass
        try:
            if loader is not None:
                return loader.get_source(environment, name)
        except TemplateNotFound:
            pass

        # at the very last, load templates from the environment
        return self.app.jinja_loader.get_source(environment, template)

    def list_templates(self):
        result = set(self.app.jinja_loader.list_templates())

        for name, module in self.app.modules.iteritems():
            if module.jinja_loader is not None:
                for template in module.jinja_loader.list_templates():
                    result.add('%s/%s' % (name, template))

        for name, blueprint in self.app.blueprints.iteritems():
            if blueprint.jinja_loader is not None:
                for template in blueprint.jinja_loader.list_templates():
                    result.add('%s:%s' % (name, template))

        return list(result)


def _render(template, context, app):
    """Renders the template and fires the signal"""
    rv = template.render(context)
    template_rendered.send(app, template=template, context=context)
    return rv


def render_template(template_name, **context):
    """Renders a template from the template folder with the given
    context.

    :param template_name: the name of the template to be rendered
    :param context: the variables that should be available in the
                    context of the template.
    """
    ctx = _request_ctx_stack.top
    ctx.app.update_template_context(context)
    if template_name[:1] == ':':
        template_name = ctx.request.blueprint + template_name
    return _render(ctx.app.jinja_env.get_template(template_name),
                   context, ctx.app)


def render_template_string(source, **context):
    """Renders a template from the given template source string
    with the given context.

    :param template_name: the sourcecode of the template to be
                          rendered
    :param context: the variables that should be available in the
                    context of the template.
    """
    ctx = _request_ctx_stack.top
    ctx.app.update_template_context(context)
    return _render(ctx.app.jinja_env.from_string(source),
                   context, ctx.app)
