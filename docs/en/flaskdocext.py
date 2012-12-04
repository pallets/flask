import re
import inspect


_internal_mark_re = re.compile(r'^\s*:internal:\s*$(?m)')


def skip_member(app, what, name, obj, skip, options):
    docstring = inspect.getdoc(obj)
    if skip:
        return True
    return _internal_mark_re.search(docstring or '') is not None


def setup(app):
    app.connect('autodoc-skip-member', skip_member)
