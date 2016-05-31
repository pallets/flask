#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    flask-07-upgrade
    ~~~~~~~~~~~~~~~~

    This command line script scans a whole application tree and attempts to
    output an unified diff with all the changes that are necessary to easily
    upgrade the application to 0.7 and to not yield deprecation warnings.

    This will also attempt to find `after_request` functions that don't modify
    the response and appear to be better suited for `teardown_request`.

    This application is indeed an incredible hack, but because what it
    attempts to accomplish is impossible to do statically it tries to support
    the most common patterns at least.  The diff it generates should be
    hand reviewed and not applied blindly without making backups.

    :copyright: (c) Copyright 2015 by Armin Ronacher.
    :license: see LICENSE for more details.
"""
from __future__ import print_function
import re
import os
import inspect
import difflib
import posixpath
from optparse import OptionParser

try:
    import ast
except ImportError:
    ast = None


TEMPLATE_LOOKAHEAD = 4096

_app_re_part = r'((?:[a-zA-Z_][a-zA-Z0-9_]*app)|app|application)'
_string_re_part = r"('([^'\\]*(?:\\.[^'\\]*)*)'" \
                  r'|"([^"\\]*(?:\\.[^"\\]*)*)")'

_from_import_re = re.compile(r'^\s*from flask import\s+')
_url_for_re = re.compile(r'\b(url_for\()(%s)' % _string_re_part)
_render_template_re = re.compile(r'\b(render_template\()(%s)' % _string_re_part)
_after_request_re = re.compile(r'((?:@\S+\.(?:app_)?))(after_request)(\b\s*$)(?m)')
_module_constructor_re = re.compile(r'([a-zA-Z0-9_][a-zA-Z0-9_]*)\s*=\s*Module'
                                    r'\(__name__\s*(?:,\s*(?:name\s*=\s*)?(%s))?' %
                                    _string_re_part)
_error_handler_re = re.compile(r'%s\.error_handlers\[\s*(\d+)\s*\]' % _app_re_part)
_mod_route_re = re.compile(r'@([a-zA-Z0-9_][a-zA-Z0-9_]*)\.route')
_blueprint_related = [
    (re.compile(r'request\.module'), 'request.blueprint'),
    (re.compile(r'register_module'), 'register_blueprint'),
    (re.compile(r'%s\.modules' % _app_re_part), '\\1.blueprints')
]


def make_diff(filename, old, new):
    for line in difflib.unified_diff(old.splitlines(), new.splitlines(),
                     posixpath.normpath(posixpath.join('a', filename)),
                     posixpath.normpath(posixpath.join('b', filename)),
                     lineterm=''):
        print(line)


def looks_like_teardown_function(node):
    returns = [x for x in ast.walk(node) if isinstance(x, ast.Return)]
    if len(returns) != 1:
        return
    return_def = returns[0]
    resp_name = node.args.args[0]
    if not isinstance(return_def.value, ast.Name) or \
       return_def.value.id != resp_name.id:
        return

    for body_node in node.body:
        for child in ast.walk(body_node):
            if isinstance(child, ast.Name) and \
               child.id == resp_name.id:
                if child is not return_def.value:
                    return

    return resp_name.id


def fix_url_for(contents, module_declarations=None):
    if module_declarations is None:
        skip_module_test = True
    else:
        skip_module_test = False
        mapping = dict(module_declarations)
    annotated_lines = []

    def make_line_annotations():
        if not annotated_lines:
            last_index = 0
            for line in contents.splitlines(True):
                last_index += len(line)
                annotated_lines.append((last_index, line))

    def backtrack_module_name(call_start):
        make_line_annotations()
        for idx, (line_end, line) in enumerate(annotated_lines):
            if line_end > call_start:
                for _, line in reversed(annotated_lines[:idx]):
                    match = _mod_route_re.search(line)
                    if match is not None:
                        shortname = match.group(1)
                        return mapping.get(shortname)

    def handle_match(match):
        if not skip_module_test:
            modname = backtrack_module_name(match.start())
            if modname is None:
                return match.group(0)
        prefix = match.group(1)
        endpoint = ast.literal_eval(match.group(2))
        if endpoint.startswith('.'):
            endpoint = endpoint[1:]
        elif '.' not in endpoint:
            endpoint = '.' + endpoint
        else:
            return match.group(0)
        return prefix + repr(endpoint)
    return _url_for_re.sub(handle_match, contents)


def fix_teardown_funcs(contents):

    def is_return_line(line):
        args = line.strip().split()
        return args and args[0] == 'return'

    def fix_single(match, lines, lineno):
        if not lines[lineno + 1].startswith('def'):
            return
        block_lines = inspect.getblock(lines[lineno + 1:])
        func_code = ''.join(block_lines)
        if func_code[0].isspace():
            node = ast.parse('if 1:\n' + func_code).body[0].body
        else:
            node = ast.parse(func_code).body[0]
        response_param_name = looks_like_teardown_function(node)
        if response_param_name is None:
            return
        before = lines[:lineno]
        decorator = [match.group(1) +
                     match.group(2).replace('after_', 'teardown_') +
                     match.group(3)]
        body = [line.replace(response_param_name, 'exception')
                for line in block_lines if
                not is_return_line(line)]
        after = lines[lineno + len(block_lines) + 1:]
        return before + decorator + body + after

    content_lines = contents.splitlines(True)
    while 1:
        found_one = False
        for idx, line in enumerate(content_lines):
            match = _after_request_re.match(line)
            if match is None:
                continue
            new_content_lines = fix_single(match, content_lines, idx)
            if new_content_lines is not None:
                content_lines = new_content_lines
                break
        else:
            break

    return ''.join(content_lines)


def get_module_autoname(filename):
    directory, filename = os.path.split(filename)
    if filename != '__init__.py':
        return os.path.splitext(filename)[0]
    return os.path.basename(directory)


def rewrite_from_imports(prefix, fromlist, lineiter):
    import_block = [prefix, fromlist]
    if fromlist[0] == '(' and fromlist[-1] != ')':
        for line in lineiter:
            import_block.append(line)
            if line.rstrip().endswith(')'):
                break
    elif fromlist[-1] == '\\':
        for line in lineiter:
            import_block.append(line)
            if line.rstrip().endswith('\\'):
                break

    return ''.join(import_block).replace('Module', 'Blueprint')


def rewrite_blueprint_imports(contents):
    new_file = []
    lineiter = iter(contents.splitlines(True))
    for line in lineiter:
        match = _from_import_re.search(line)
        if match is not None:
            new_file.extend(rewrite_from_imports(match.group(),
                                                 line[match.end():],
                                                 lineiter))
        else:
            new_file.append(line)
    return ''.join(new_file)


def rewrite_for_blueprints(contents, filename):
    modules_declared = []
    def handle_match(match):
        target = match.group(1)
        name_param = match.group(2)
        if name_param is None:
            modname = get_module_autoname(filename)
        else:
            modname = ast.literal_eval(name_param)
        modules_declared.append((target, modname))
        return '%s = %s' % (target, 'Blueprint(%r, __name__' % modname)
    new_contents = _module_constructor_re.sub(handle_match, contents)

    if modules_declared:
        new_contents = rewrite_blueprint_imports(new_contents)

    for pattern, replacement in _blueprint_related:
        new_contents = pattern.sub(replacement, new_contents)
    return new_contents, dict(modules_declared)


def upgrade_python_file(filename, contents, teardown):
    new_contents = contents
    if teardown:
        new_contents = fix_teardown_funcs(new_contents)
    new_contents, modules = rewrite_for_blueprints(new_contents, filename)
    new_contents = fix_url_for(new_contents, modules)
    new_contents = _error_handler_re.sub('\\1.error_handler_spec[None][\\2]',
                                         new_contents)
    make_diff(filename, contents, new_contents)


def upgrade_template_file(filename, contents):
    new_contents = fix_url_for(contents, None)
    make_diff(filename, contents, new_contents)


def walk_path(path):
    this_file = os.path.realpath(__file__).rstrip('c')
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [x for x in dirnames if not x.startswith('.')]
        for filename in filenames:
            filename = os.path.join(dirpath, filename)
            if os.path.realpath(filename) == this_file:
                continue
            if filename.endswith('.py'):
                yield filename, 'python'
            # skip files that are diffs.  These might be false positives
            # when run multiple times.
            elif not filename.endswith(('.diff', '.patch', '.udiff')):
                with open(filename) as f:
                    contents = f.read(TEMPLATE_LOOKAHEAD)
                if '{% for' or '{% if' or '{{ url_for' in contents:
                    yield filename, 'template'


def scan_path(path=None, teardown=True):
    for filename, type in walk_path(path):
        with open(filename) as f:
            contents = f.read()
        if type == 'python':
            upgrade_python_file(filename, contents, teardown)
        elif type == 'template':
            upgrade_template_file(filename, contents)


def main():
    """Entrypoint"""
    parser = OptionParser(usage='%prog [options] [paths]')
    parser.add_option('-T', '--no-teardown-detection', dest='no_teardown',
                      action='store_true', help='Do not attempt to '
                      'detect teardown function rewrites.')
    parser.add_option('-b', '--bundled-templates', dest='bundled_tmpl',
                      action='store_true', help='Indicate to the system '
                      'that templates are bundled with modules.  Default '
                      'is auto detect.')
    options, args = parser.parse_args()
    if not args:
        args = ['.']

    if ast is None:
        parser.error('Python 2.6 or later is required to run the upgrade script.')

    for path in args:
        scan_path(path, teardown=not options.no_teardown)


if __name__ == '__main__':
    main()
