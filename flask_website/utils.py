import re
import creoleparser
from datetime import datetime, timedelta
from genshi import builder
from functools import wraps
from creoleparser.elements import PreBlock
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound
from flask import g, url_for, flash, abort, request, redirect, Markup
from flask_website.flaskystyle import FlaskyStyle # same as docs


pygments_formatter = HtmlFormatter(style=FlaskyStyle)

_ws_split_re = re.compile(r'(\s+)')


TIMEDELTA_UNITS = (
    ('year',   3600 * 24 * 365),
    ('month',  3600 * 24 * 30),
    ('week',   3600 * 24 * 7),
    ('day',    3600 * 24),
    ('hour',   3600),
    ('minute', 60),
    ('second', 1)
)


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
# hacky way to get rid of image support
custom_dialect.img = custom_dialect.no_wiki
custom_dialect.pre = CodeBlock()


_parser = creoleparser.Parser(
    dialect=custom_dialect,
    method='html'
)


def format_creole(text):
    return Markup(_parser.render(text, encoding=None))


def split_lines_wrapping(text, width=74, threshold=82):
    lines = text.splitlines()
    if all(len(line) <= threshold for line in lines):
        return lines
    result = []
    for line in lines:
        if len(line) <= threshold:
            result.append(line)
            continue
        line_width = 0
        line_buffer = []
        for piece in _ws_split_re.split(line):
            line_width += len(piece)
            if line_width > width:
                result.append(u''.join(line_buffer))
                line_buffer = []
                if not piece.isspace():
                    line_buffer.append(piece)
                    line_width = len(piece)
                else:
                    line_width = 0
            else:
                line_buffer.append(piece)
        if line_buffer:
            result.append(u''.join(line_buffer))
    return result


def request_wants_json():
    # we only accept json if the quality of json is greater than the
    # quality of text/html because text/html is preferred to support
    # browsers that accept on */*
    best = request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
       request.accept_mimetypes[best] > request.accept_mimetypes['text/html']


def requires_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            flash(u'You need to be signed in for this page.')
            return redirect(url_for('general.login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function


def requires_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user.is_admin:
            abort(401)
        return f(*args, **kwargs)
    return requires_login(decorated_function)


def format_datetime(dt):
    return dt.strftime('%Y-%m-%d @ %H:%M')


def format_timedelta(delta, granularity='second', threshold=.85):
    if isinstance(delta, datetime):
        delta = datetime.utcnow() - delta
    if isinstance(delta, timedelta):
        seconds = int((delta.days * 86400) + delta.seconds)
    else:
        seconds = delta

    for unit, secs_per_unit in TIMEDELTA_UNITS:
        value = abs(seconds) / secs_per_unit
        if value >= threshold or unit == granularity:
            if unit == granularity and value > 0:
                value = max(1, value)
            value = int(round(value))
            rv = u'%s %s' % (value, unit)
            if value != 1:
                rv += u's'
            return rv
    return u''


def display_openid(openid):
    if not openid:
        return ''
    rv = openid
    if rv.startswith(('http://', 'https://')):
        rv = rv.split('/', 2)[-1]
    return rv.rstrip('/')
