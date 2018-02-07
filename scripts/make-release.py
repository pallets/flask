#!/usr/bin/env python
from __future__ import print_function

import os
import re
import sys
from datetime import date, datetime
from subprocess import PIPE, Popen

_date_strip_re = re.compile(r'(?<=\d)(st|nd|rd|th)')


def parse_changelog():
    with open('CHANGES.rst') as f:
        lineiter = iter(f)
        for line in lineiter:
            match = re.search('^Version\s+(.*)', line.strip())

            if match is None:
                continue

            version = match.group(1).strip()

            if next(lineiter).count('-') != len(match.group(0)):
                continue

            while 1:
                change_info = next(lineiter).strip()

                if change_info:
                    break

            match = re.search(
                r'released on (\w+\s+\d+\w+\s+\d+)(?:, codename (.*))?',
                change_info,
                flags=re.IGNORECASE
            )

            if match is None:
                continue

            datestr, codename = match.groups()
            return version, parse_date(datestr), codename


def bump_version(version):
    try:
        parts = [int(i) for i in version.split('.')]
    except ValueError:
        fail('Current version is not numeric')

    parts[-1] += 1
    return '.'.join(map(str, parts))


def parse_date(string):
    string = _date_strip_re.sub('', string)
    return datetime.strptime(string, '%B %d %Y')


def set_filename_version(filename, version_number, pattern):
    changed = []

    def inject_version(match):
        before, old, after = match.groups()
        changed.append(True)
        return before + version_number + after

    with open(filename) as f:
        contents = re.sub(
            r"^(\s*%s\s*=\s*')(.+?)(')" % pattern,
            inject_version, f.read(),
            flags=re.DOTALL | re.MULTILINE
        )

    if not changed:
        fail('Could not find %s in %s', pattern, filename)

    with open(filename, 'w') as f:
        f.write(contents)


def set_init_version(version):
    info('Setting __init__.py version to %s', version)
    set_filename_version('flask/__init__.py', version, '__version__')


def build():
    cmd = [sys.executable, 'setup.py', 'sdist', 'bdist_wheel']
    Popen(cmd).wait()


def fail(message, *args):
    print('Error:', message % args, file=sys.stderr)
    sys.exit(1)


def info(message, *args):
    print(message % args, file=sys.stderr)


def get_git_tags():
    return set(
        Popen(['git', 'tag'], stdout=PIPE).communicate()[0].splitlines()
    )


def git_is_clean():
    return Popen(['git', 'diff', '--quiet']).wait() == 0


def make_git_commit(message, *args):
    message = message % args
    Popen(['git', 'commit', '-am', message]).wait()


def make_git_tag(tag):
    info('Tagging "%s"', tag)
    Popen(['git', 'tag', tag]).wait()


def main():
    os.chdir(os.path.join(os.path.dirname(__file__), '..'))

    rv = parse_changelog()

    if rv is None:
        fail('Could not parse changelog')

    version, release_date, codename = rv
    dev_version = bump_version(version) + '.dev'

    info(
        'Releasing %s (codename %s, release date %s)',
        version, codename, release_date.strftime('%d/%m/%Y')
    )
    tags = get_git_tags()

    if version in tags:
        fail('Version "%s" is already tagged', version)

    if release_date.date() != date.today():
        fail(
            'Release date is not today (%s != %s)',
            release_date.date(), date.today()
        )

    if not git_is_clean():
        fail('You have uncommitted changes in git')

    try:
        import wheel  # noqa: F401
    except ImportError:
        fail('You need to install the wheel package.')

    set_init_version(version)
    make_git_commit('Bump version number to %s', version)
    make_git_tag(version)
    build()
    set_init_version(dev_version)


if __name__ == '__main__':
    main()
