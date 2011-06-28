# -*- coding: utf-8 -*-
"""
    flask.views
    ~~~~~~~~~~~

    This module provides class based views inspired by the ones in Django.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from .globals import request


http_method_funcs = frozenset(['get', 'post', 'head', 'options',
                               'delete', 'put', 'trace'])



class View(object):
    """Alternative way to use view functions.  A subclass has to implement
    :meth:`dispatch_request` which is called with the view arguments from
    the URL routing system.  If :attr:`methods` is provided the methods
    do not have to be passed to the :meth:`~flask.Flask.add_url_rule`
    method explicitly::

        class MyView(View):
            methods = ['GET']

            def dispatch_request(self, name):
                return 'Hello %s!' % name

        app.add_url_rule('/hello/<name>', view_func=MyView.as_view('myview'))
    """

    methods = None

    def dispatch_request(self):
        """Subclasses have to override this method to implement the
        actual view functionc ode.  This method is called with all
        the arguments from the URL rule.
        """
        raise NotImplementedError()

    @classmethod
    def as_view(cls, name, *class_args, **class_kwargs):
        """Converts the class into an actual view function that can be
        used with the routing system.  What it does internally is generating
        a function on the fly that will instanciate the :class:`View`
        on each request and call the :meth:`dispatch_request` method on it.

        The arguments passed to :meth:`as_view` are forwarded to the
        constructor of the class.
        """
        def view(*args, **kwargs):
            self = view.view_class(*class_args, **class_kwargs)
            return self.dispatch_request(*args, **kwargs)
        # we attach the view class to the view function for two reasons:
        # first of all it allows us to easily figure out what class based
        # view this thing came from, secondly it's also used for instanciating
        # the view class so you can actually replace it with something else
        # for testing purposes and debugging.
        view.view_class = cls
        view.__name__ = name
        view.__doc__ = cls.__doc__
        view.__module__ = cls.__module__
        view.methods = cls.methods
        return view


class MethodViewType(type):

    def __new__(cls, name, bases, d):
        rv = type.__new__(cls, name, bases, d)
        if 'methods' not in d:
            methods = set(rv.methods or [])
            for key, value in d.iteritems():
                if key in http_method_funcs:
                    methods.add(key.upper())
            # if we have no method at all in there we don't want to
            # add a method list.  (This is for instance the case for
            # the baseclass or another subclass of a base method view
            # that does not introduce new methods).
            if methods:
                rv.methods = sorted(methods)
        return rv


class MethodView(View):
    """Like a regular class based view but that dispatches requests to
    particular methods.  For instance if you implement a method called
    :meth:`get` it means you will response to ``'GET'`` requests and
    the :meth:`dispatch_request` implementation will automatically
    forward your request to that.  Also :attr:`options` is set for you
    automatically::

        class CounterAPI(MethodView):

            def get(self):
                return session.get('counter', 0)

            def post(self):
                session['counter'] = session.get('counter', 0) + 1
                return 'OK'

        app.add_url_rule('/counter', view_func=CounterAPI.as_view('counter'))
    """
    __metaclass__ = MethodViewType

    def dispatch_request(self, *args, **kwargs):
        meth = getattr(self, request.method.lower(), None)
        assert meth is not None, 'Not implemented method'
        return meth(*args, **kwargs)
