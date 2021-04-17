.. _asgi:

ASGI
====

If you'd like to use an ASGI server you will need to utilise WSGI to
ASGI middleware. The asgiref
[WsgiToAsgi](https://github.com/django/asgiref#wsgi-to-asgi-adapter)
adapter is recommended as it integrates with the event loop used for
Flask's :ref:`async_await` support. You can use the adapter by
wrapping the Flask app,

.. code-block:: python

    from asgiref.wsgi import WsgiToAsgi
    from flask import Flask

    app = Flask(__name__)

    ...

    asgi_app = WsgiToAsgi(app)

and then serving the ``asgi_app`` with the asgi server, e.g. using
`Hypercorn <https://gitlab.com/pgjones/hypercorn>`_,

.. sourcecode:: text

    $ hypercorn module:asgi_app
