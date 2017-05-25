from __future__ import absolute_import, print_function

from flask import Flask


def create_app():
    return Flask('create_app')


def create_app2(foo, bar):
    return Flask("_".join(['create_app2', foo, bar]))


def create_app3(foo, bar, script_info):
    return Flask("_".join(['create_app3', foo, bar]))
