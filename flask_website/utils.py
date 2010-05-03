import creoleparser
from genshi import builder
from functools import wraps
from creoleparser.elements import PreBlock
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound
from flask import g, url_for, flash, request, redirect, Markup
from flask_website.flaskystyle import FlaskyStyle # same as docs

from flask_website.database import User

pygments_formatter = HtmlFormatter(style=FlaskyStyle)


class CodeBlock(PreBlock):

    def __init__(self):
        super(CodeBlock, self).__init__('pre', ['{{{', '}}}'])

    def _build(self, mo, element_store, environ):
        lines = self.regexp2.sub(r'\1', mo.group(1)).splitlines()
        if lines and lines[0].startswith('#!'):
            try:
                lexer = get_lexer_by_name(lines.pop(0)[2:].strip())
            except ClassNotFound:
                pass
            else:
                return Markup(highlight(u'\n'.join(lines), lexer,
                                        pygments_formatter))
        return builder.tag.pre(u'\n'.join(lines))


custom_dialect = creoleparser.create_dialect(creoleparser.creole10_base)
custom_dialect.pre = CodeBlock()


_parser = creoleparser.Parser(
    dialect=custom_dialect,
    method='html'
)


def format_creole(text):
    return Markup(_parser.render(text, encoding=None))


def requires_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            flash(u'You need to be signed in for this page.')
            return redirect(url_for('general.login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function
