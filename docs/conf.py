# -*- coding: utf-8 -*-
from __future__ import print_function

import inspect
import re

from pallets_sphinx_themes import DocVersion, ProjectLink, get_version

# Project --------------------------------------------------------------

project = 'Flask'
copyright = '2010 Pallets Team'
author = 'Pallets Team'
release, version = get_version('Flask')

# General --------------------------------------------------------------

master_doc = 'index'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinxcontrib.log_cabinet',
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'werkzeug': ('http://werkzeug.pocoo.org/docs/', None),
    'click': ('http://click.pocoo.org/', None),
    'jinja': ('http://jinja.pocoo.org/docs/', None),
    'itsdangerous': ('https://pythonhosted.org/itsdangerous', None),
    'sqlalchemy': ('https://docs.sqlalchemy.org/en/latest/', None),
    'wtforms': ('https://wtforms.readthedocs.io/en/latest/', None),
    'blinker': ('https://pythonhosted.org/blinker/', None),
}

# HTML -----------------------------------------------------------------

html_theme = 'flask'
html_context = {
    'project_links': [
        ProjectLink('Donate to Pallets', 'https://psfmember.org/civicrm/contribute/transact?reset=1&id=20'),
        ProjectLink('Flask Website', 'https://palletsprojects.com/p/flask/'),
        ProjectLink('PyPI releases', 'https://pypi.org/project/Flask/'),
        ProjectLink('Source Code', 'https://github.com/pallets/flask/'),
        ProjectLink(
            'Issue Tracker', 'https://github.com/pallets/flask/issues/'),
    ],
    'versions': [
        DocVersion('dev', 'Development', 'unstable'),
        DocVersion('1.0', 'Flask 1.0', 'stable'),
        DocVersion('0.12', 'Flask 0.12'),
    ],
    'canonical_url': 'http://flask.pocoo.org/docs/{}/'.format(version),
    'carbon_ads_args': 'zoneid=1673&serve=C6AILKT&placement=pocooorg',
}
html_sidebars = {
    'index': [
        'project.html',
        'versions.html',
        'carbon_ads.html',
        'searchbox.html',
    ],
    '**': [
        'localtoc.html',
        'relations.html',
        'versions.html',
        'carbon_ads.html',
        'searchbox.html',
    ]
}
html_static_path = ['_static']
html_favicon = '_static/flask-favicon.ico'
html_logo = '_static/flask.png'
html_additional_pages = {
    '404': '404.html',
}
html_show_sourcelink = False

# LaTeX ----------------------------------------------------------------

latex_documents = [
    (master_doc, 'Flask.tex', 'Flask Documentation', 'Pallets Team', 'manual'),
]
latex_use_modindex = False
latex_elements = {
    'papersize': 'a4paper',
    'pointsize': '12pt',
    'fontpkg': r'\usepackage{mathpazo}',
    'preamble': r'\usepackage{flaskstyle}',
}
latex_use_parts = True
latex_additional_files = ['flaskstyle.sty', 'logo.pdf']

# linkcheck ------------------------------------------------------------

linkcheck_anchors = False

# Local Extensions -----------------------------------------------------

def unwrap_decorators():
    import sphinx.util.inspect as inspect
    import functools

    old_getargspec = inspect.getargspec
    def getargspec(x):
        return old_getargspec(getattr(x, '_original_function', x))
    inspect.getargspec = getargspec

    old_update_wrapper = functools.update_wrapper
    def update_wrapper(wrapper, wrapped, *a, **kw):
        rv = old_update_wrapper(wrapper, wrapped, *a, **kw)
        rv._original_function = wrapped
        return rv
    functools.update_wrapper = update_wrapper


unwrap_decorators()
del unwrap_decorators


_internal_mark_re = re.compile(r'^\s*:internal:\s*$(?m)', re.M)


def skip_internal(app, what, name, obj, skip, options):
    docstring = inspect.getdoc(obj) or ''

    if skip or _internal_mark_re.search(docstring) is not None:
        return True


def cut_module_meta(app, what, name, obj, options, lines):
    """Remove metadata from autodoc output."""
    if what != 'module':
        return

    lines[:] = [
        line for line in lines
        if not line.startswith((':copyright:', ':license:'))
    ]


def github_link(
    name, rawtext, text, lineno, inliner, options=None, content=None
):
    app = inliner.document.settings.env.app
    release = app.config.release
    base_url = 'https://github.com/pallets/flask/tree/'

    if text.endswith('>'):
        words, text = text[:-1].rsplit('<', 1)
        words = words.strip()
    else:
        words = None

    if release.endswith('dev'):
        url = '{0}master/{1}'.format(base_url, text)
    else:
        url = '{0}{1}/{2}'.format(base_url, release, text)

    if words is None:
        words = url

    from docutils.nodes import reference
    from docutils.parsers.rst.roles import set_classes
    options = options or {}
    set_classes(options)
    node = reference(rawtext, words, refuri=url, **options)
    return [node], []


def setup(app):
    app.connect('autodoc-skip-member', skip_internal)
    app.connect('autodoc-process-docstring', cut_module_meta)
    app.add_role('gh', github_link)
