from flask import Flask


def create_app():
    return Flask("app")


def create_app2(foo, bar):
    return Flask("_".join(["app2", foo, bar]))


def no_app():
    pass
