Subclassing Flask
=================

The :class:`~flask.Flask` class is designed for subclassing.

For example, you may want to override how request parameters are handled to preserve their order::

    from flask import Flask, Request
    from werkzeug.datastructures import ImmutableOrderedMultiDict
    class MyRequest(Request):
        """Request subclass to override request parameter storage"""
        parameter_storage_class = ImmutableOrderedMultiDict
    class MyFlask(Flask):
        """Flask subclass using the custom request class"""
        request_class = MyRequest

This is the recommended approach for overriding or augmenting Flask's internal functionality.
