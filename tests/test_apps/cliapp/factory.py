from __future__ import absolute_import
from __future__ import print_function

from flask import Flask


def create_app():
    return Flask("app")


def create_app2(foo, bar):
    return Flask("_".join(["app2", foo, bar]))


def create_app3(foo, script_info):
    return Flask("_".join(["app3", foo, script_info.data["test"]]))


def no_app():
    pass
