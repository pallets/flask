from pallets_sphinx_themes import get_version
from pallets_sphinx_themes import ProjectLink

# Project --------------------------------------------------------------

project = "Flask"
copyright = "2010 Pallets"
author = "Pallets"
release, version = get_version("Flask")

# General --------------------------------------------------------------

master_doc = "index"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinxcontrib.log_cabinet",
    "pallets_sphinx_themes",
    "sphinx_issues",
]
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "werkzeug": ("https://werkzeug.palletsprojects.com/", None),
    "click": ("https://click.palletsprojects.com/", None),
    "jinja": ("http://jinja.pocoo.org/docs/", None),
    "itsdangerous": ("https://itsdangerous.palletsprojects.com/", None),
    "sqlalchemy": ("https://docs.sqlalchemy.org/", None),
    "wtforms": ("https://wtforms.readthedocs.io/en/stable/", None),
    "blinker": ("https://pythonhosted.org/blinker/", None),
}
issues_github_path = "pallets/flask"

# HTML -----------------------------------------------------------------

html_theme = "flask"
html_theme_options = {"index_sidebar_logo": False}
html_context = {
    "project_links": [
        ProjectLink("Donate to Pallets", "https://palletsprojects.com/donate"),
        ProjectLink("Flask Website", "https://palletsprojects.com/p/flask/"),
        ProjectLink("PyPI releases", "https://pypi.org/project/Flask/"),
        ProjectLink("Source Code", "https://github.com/pallets/flask/"),
        ProjectLink("Issue Tracker", "https://github.com/pallets/flask/issues/"),
    ]
}
html_sidebars = {
    "index": ["project.html", "localtoc.html", "searchbox.html"],
    "**": ["localtoc.html", "relations.html", "searchbox.html"],
}
singlehtml_sidebars = {"index": ["project.html", "localtoc.html"]}
html_static_path = ["_static"]
html_favicon = "_static/flask-icon.png"
html_logo = "_static/flask-icon.png"
html_title = "Flask Documentation ({})".format(version)
html_show_sourcelink = False

# LaTeX ----------------------------------------------------------------

latex_documents = [
    (master_doc, "Flask-{}.tex".format(version), html_title, author, "manual")
]

# Local Extensions -----------------------------------------------------


def github_link(name, rawtext, text, lineno, inliner, options=None, content=None):
    app = inliner.document.settings.env.app
    release = app.config.release
    base_url = "https://github.com/pallets/flask/tree/"

    if text.endswith(">"):
        words, text = text[:-1].rsplit("<", 1)
        words = words.strip()
    else:
        words = None

    if release.endswith("dev"):
        url = "{0}master/{1}".format(base_url, text)
    else:
        url = "{0}{1}/{2}".format(base_url, release, text)

    if words is None:
        words = url

    from docutils.nodes import reference
    from docutils.parsers.rst.roles import set_classes

    options = options or {}
    set_classes(options)
    node = reference(rawtext, words, refuri=url, **options)
    return [node], []


def setup(app):
    app.add_role("gh", github_link)
