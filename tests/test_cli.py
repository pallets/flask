# -*- coding: utf-8 -*-
"""
    tests.cli
    ~~~~~~~~~~~~

    Tests the flask CLI.

    :copyright: (c) 2015 by the Flask Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import glob
import os
from random import sample
import re
import string
from subprocess import Popen, PIPE
from textwrap import dedent


def test_cli_no_arg_custom_command_help():
    app_name_suffix = ''.join(sample(string.ascii_letters, 12))
    app_name = 'cli_no_arg_custom_command_help_{0}'.format(app_name_suffix)
    command_name = 'somecustomcommand'
    command_help = 'Some custom command help'
    fmt_kwargs = locals()
    app_file_contents = dedent('''\
    import flask

    app = flask.Flask('{app_name}')

    @app.cli.command()
    def {command_name}():
        """ {command_help} """

        print('some custom output')
        return True
    '''.format(**fmt_kwargs))
    command_help_re = r'{command_name}\s+{command_help}'.format(**fmt_kwargs)

    # write app module file
    with open('{0}.py'.format(app_name), 'w') as app_file:
        app_file.write(app_file_contents)

    # run flask cli with no args
    env = dict(os.environ)
    env['FLASK_APP'] = app_name
    popen_args = ['flask']
    no_arg_output = Popen(popen_args, stdout=PIPE, env=env).communicate()[0]
    if hasattr(no_arg_output, 'decode'):
        no_arg_output = no_arg_output.decode('utf8')

    # remove app module files
    app_filenames = glob.glob('{0}.py*'.format(app_name))
    for app_filename in app_filenames:
        os.remove(app_filename)

    # search for custom command help
    custom_help_match = re.search(command_help_re, no_arg_output)

    assert bool(custom_help_match)

    custom_help_should = '{command_name} {command_help}'.format(**fmt_kwargs)
    custom_help_actual = re.sub(r'\s+', ' ', custom_help_match.group(0))

    assert custom_help_should == custom_help_actual
