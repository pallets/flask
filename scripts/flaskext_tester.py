# -*- coding: utf-8 -*-
"""
    Flask Extension Tests
    ~~~~~~~~~~~~~~~~~~~~~

    Tests the Flask extensions.

    :copyright: (c) 2015 by Ali Afshar.
    :license: BSD, see LICENSE for more details.
"""

import os
import sys
import shutil
import urllib2
import tempfile
import subprocess
import argparse

from flask import json

from setuptools.package_index import PackageIndex
from setuptools.archive_util import unpack_archive

flask_svc_url = 'http://flask.pocoo.org/extensions/'


# OS X has awful paths when using mkstemp or gettempdir().  I don't
# care about security or clashes here, so pick something that is
# actually memorable.
if sys.platform == 'darwin':
    _tempdir = '/private/tmp'
else:
    _tempdir = tempfile.gettempdir()
tdir = _tempdir + '/flaskext-test'
flaskdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


# virtualenv hack *cough*
os.environ['PYTHONDONTWRITEBYTECODE'] = ''


RESULT_TEMPATE = u'''\
<!doctype html>
<title>Flask-Extension Test Results</title>
<style type=text/css>
  body         { font-family: 'Georgia', serif; font-size: 17px; color: #000; }
  a            { color: #004B6B; }
  a:hover      { color: #6D4100; }
  h1, h2, h3   { font-family: 'Garamond', 'Georgia', serif; font-weight: normal; }
  h1           { font-size: 30px; margin: 15px 0 5px 0; }
  h2           { font-size: 24px; margin: 15px 0 5px 0; }
  h3           { font-size: 19px; margin: 15px 0 5px 0; }
  textarea, code,
  pre          { font-family: 'Consolas', 'Menlo', 'Deja Vu Sans Mono',
                 'Bitstream Vera Sans Mono', monospace!important; font-size: 15px;
                 background: #eee; }
  pre          { padding: 7px 15px; line-height: 1.3; }
  p            { line-height: 1.4; }
  table        { border: 1px solid black; border-collapse: collapse;
                 margin: 15px 0; }
  td, th       { border: 1px solid black; padding: 4px 10px;
                 text-align: left; }
  th           { background: #eee; font-weight: normal; }
  tr.success   { background: #D3F5CC; }
  tr.failed    { background: #F5D2CB; }
</style>
<h1>Flask-Extension Test Results</h1>
<p>
  This page contains the detailed test results for the test run of
  all {{ 'approved' if approved }} Flask extensions.
<h2>Summary</h2>
<table class=results>
  <thead>
    <tr>
      <th>Extension
      <th>Version
      <th>Author
      <th>License
      <th>Outcome
      {%- for iptr, _ in results[0].logs|dictsort %}
        <th>{{ iptr }}
      {%- endfor %}
    </tr>
  </thead>
  <tbody>
  {%- for result in results %}
    {% set outcome = 'success' if result.success else 'failed' %}
    <tr class={{ outcome }}>
      <th>{{ result.name }}
      <td>{{ result.version }}
      <td>{{ result.author }}
      <td>{{ result.license }}
      <td>{{ outcome }}
      {%- for iptr, _ in result.logs|dictsort %}
        <td><a href="#{{ result.name }}-{{ iptr }}">see log</a>
      {%- endfor %}
    </tr>
  {%- endfor %}
  </tbody>
</table>
<h2>Test Logs</h2>
<p>Detailed test logs for all tests on all platforms:
{%- for result in results %}
  {%- for iptr, log in result.logs|dictsort %}
    <h3 id="{{ result.name }}-{{ iptr }}">
      {{ result.name }} - {{ result.version }} [{{ iptr }}]</h3>
    <pre>{{ log }}</pre>
  {%- endfor %}
{%- endfor %}
'''


def log(msg, *args):
    print('[EXTTEST] ' + (msg % args))


class TestResult(object):

    def __init__(self, name, folder, statuscode, interpreters):
        intrptr = os.path.join(folder, '.tox/%s/bin/python'
                               % interpreters[0])
        self.statuscode = statuscode
        self.folder = folder
        self.success = statuscode == 0

        def fetch(field):
            try:
                c = subprocess.Popen([intrptr, 'setup.py',
                                      '--' + field], cwd=folder,
                                      stdout=subprocess.PIPE)
                return c.communicate()[0].strip()
            except OSError:
                return '?'
        self.name = name
        self.license = fetch('license')
        self.author = fetch('author')
        self.version = fetch('version')

        self.logs = {}
        for interpreter in interpreters:
            logfile = os.path.join(folder, '.tox/%s/log/test.log'
                                   % interpreter)
            if os.path.isfile(logfile):
                self.logs[interpreter] = open(logfile).read()
            else:
                self.logs[interpreter] = ''


def create_tdir():
    try:
        shutil.rmtree(tdir)
    except Exception:
        pass
    os.mkdir(tdir)


def package_flask():
    distfolder = tdir + '/.flask-dist'
    c = subprocess.Popen(['python', 'setup.py', 'sdist', '--formats=gztar',
                          '--dist', distfolder], cwd=flaskdir)
    c.wait()
    return os.path.join(distfolder, os.listdir(distfolder)[0])


def get_test_command(checkout_dir):
    if os.path.isfile(checkout_dir + '/Makefile'):
        return 'make test'
    return 'python setup.py test'


def fetch_extensions_list():
    req = urllib2.Request(flask_svc_url, headers={'accept':'application/json'})
    d = urllib2.urlopen(req).read()
    data = json.loads(d)
    for ext in data['extensions']:
        yield ext


def checkout_extension(name):
    log('Downloading extension %s to temporary folder', name)
    root = os.path.join(tdir, name)
    os.mkdir(root)
    checkout_path = PackageIndex().download(name, root)

    unpack_archive(checkout_path, root)
    path = None
    for fn in os.listdir(root):
        path = os.path.join(root, fn)
        if os.path.isdir(path):
            break
    log('Downloaded to %s', path)
    return path


tox_template = """[tox]
envlist=%(env)s

[testenv]
deps=
  %(deps)s
  distribute
  py
commands=bash flaskext-runtest.sh {envlogdir}/test.log
downloadcache=%(cache)s
"""


def create_tox_ini(checkout_path, interpreters, flask_dep):
    tox_path = os.path.join(checkout_path, 'tox-flask-test.ini')
    if not os.path.exists(tox_path):
        with open(tox_path, 'w') as f:
            f.write(tox_template % {
                'env':      ','.join(interpreters),
                'cache':    tdir,
                'deps':     flask_dep
            })
    return tox_path


def iter_extensions(only_approved=True):
    for ext in fetch_extensions_list():
        if ext['approved'] or not only_approved:
            yield ext['name']


def test_extension(name, interpreters, flask_dep):
    checkout_path = checkout_extension(name)
    log('Running tests with tox in %s', checkout_path)

    # figure out the test command and write a wrapper script.  We
    # can't write that directly into the tox ini because tox does
    # not invoke the command from the shell so we have no chance
    # to pipe the output into a logfile.  The /dev/null hack is
    # to trick py.test (if used) into not guessing widths from the
    # invoking terminal.
    test_command = get_test_command(checkout_path)
    log('Test command: %s', test_command)
    f = open(checkout_path + '/flaskext-runtest.sh', 'w')
    f.write(test_command + ' &> "$1" < /dev/null\n')
    f.close()

    # if there is a tox.ini, remove it, it will cause troubles
    # for us.  Remove it if present, we are running tox ourselves
    # afterall.

    create_tox_ini(checkout_path, interpreters, flask_dep)
    rv = subprocess.call(['tox', '-c', 'tox-flask-test.ini'], cwd=checkout_path)
    return TestResult(name, checkout_path, rv, interpreters)


def run_tests(extensions, interpreters):
    results = {}
    create_tdir()
    log('Packaging Flask')
    flask_dep = package_flask()
    log('Running extension tests')
    log('Temporary Environment: %s', tdir)
    for name in extensions:
        log('Testing %s', name)
        result = test_extension(name, interpreters, flask_dep)
        if result.success:
            log('Extension test succeeded')
        else:
            log('Extension test failed')
        results[name] = result
    return results


def render_results(results, approved):
    from jinja2 import Template
    items = results.values()
    items.sort(key=lambda x: x.name.lower())
    rv = Template(RESULT_TEMPATE, autoescape=True).render(results=items,
                                                          approved=approved)
    fd, filename = tempfile.mkstemp(suffix='.html')
    os.fdopen(fd, 'w').write(rv.encode('utf-8') + '\n')
    return filename


def main():
    parser = argparse.ArgumentParser(description='Runs Flask extension tests')
    parser.add_argument('--all', dest='all', action='store_true',
                        help='run against all extensions, not just approved')
    parser.add_argument('--browse', dest='browse', action='store_true',
                        help='show browser with the result summary')
    parser.add_argument('--env', dest='env', default='py25,py26,py27',
                        help='the tox environments to run against')
    parser.add_argument('--extension=', dest='extension', default=None,
                        help='tests a single extension')
    args = parser.parse_args()

    if args.extension is not None:
        only_approved = False
        extensions = [args.extension]
    else:
        only_approved = not args.all
        extensions = iter_extensions(only_approved)

    results = run_tests(extensions, [x.strip() for x in args.env.split(',')])
    filename = render_results(results, only_approved)
    if args.browse:
        import webbrowser
        webbrowser.open('file:///' + filename.lstrip('/'))
    print('Results written to {}'.format(filename))


if __name__ == '__main__':
    main()
