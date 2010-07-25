# -*- coding: utf-8 -*-
"""
    Flask Extension Tests
    ~~~~~~~~~~~~~~~~~~~~~

    Tests the Flask extensions.

    :copyright: (c) 2010 by Ali Afshar.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import with_statement

import tempfile, subprocess, urllib2, os

from flask import json

from setuptools.package_index import PackageIndex
from setuptools.archive_util import unpack_archive

flask_svc_url = 'http://flask.pocoo.org/extensions/'
tdir = tempfile.mkdtemp()


def run_tests(checkout_dir):
    cmd = ['tox']
    return subprocess.call(cmd, cwd=checkout_dir,
                           stdout=open(os.path.join(tdir, 'tox.log'), 'w'),
                           stderr=subprocess.STDOUT)


def get_test_command(checkout_dir):
    files = set(os.listdir(checkout_dir))
    if 'Makefile' in files:
        return 'make test'
    elif 'conftest.py' in files:
        return 'py.test'
    else:
        return 'nosetests'


def fetch_extensions_list():
    req = urllib2.Request(flask_svc_url, headers={'accept':'application/json'})
    d = urllib2.urlopen(req).read()
    data = json.loads(d)
    for ext in data['extensions']:
        yield ext


def checkout_extension(ext):
    name = ext['name']
    root = os.path.join(tdir, name)
    os.mkdir(root)
    checkout_path = PackageIndex().download(ext['name'], root)
    unpack_archive(checkout_path, root)
    path = None
    for fn in os.listdir(root):
        path = os.path.join(root, fn)
        if os.path.isdir(path):
            break
    return path


tox_template = """[tox]
envlist=py26

[testenv]
commands=
%s
downloadcache=
%s
"""

def create_tox_ini(checkout_path):
    tox_path = os.path.join(checkout_path, 'tox.ini')
    if not os.path.exists(tox_path):
        with open(tox_path, 'w') as f:
            f.write(tox_template % (get_test_command(checkout_path), tdir))

# XXX command line
only_approved = True

def test_all_extensions(only_approved=only_approved):
    for ext in fetch_extensions_list():
        if ext['approved'] or not only_approved:
            checkout_path = checkout_extension(ext)
            create_tox_ini(checkout_path)
            ret = run_tests(checkout_path)
            yield ext['name'], ret

def main():
    for name, ret in test_all_extensions():
        print name, ret


if __name__ == '__main__':
    main()
