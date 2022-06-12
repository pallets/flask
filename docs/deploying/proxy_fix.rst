Tell Flask it is Behind a Proxy
===============================

When using a reverse proxy, or many Python hosting platforms, the proxy
will intercept and forward all external requests to the local WSGI
server.

From the WSGI server and Flask application's perspectives, requests are
now coming from the HTTP server to the local address, rather than from
the remote address to the external server address.

HTTP servers should set ``X-Forwarded-`` headers to pass on the real
values to the application. The application can then be told to trust and
use those values by wrapping it with the
:doc:`werkzeug:middleware/proxy_fix` middleware provided by Werkzeug.

This middleware should only be used if the application is actually
behind a proxy, and should be configured with the number of proxies that
are chained in front of it. Not all proxies set all the headers. Since
incoming headers can be faked, you must set how many proxies are setting
each header so the middleware knows what to trust.

.. code-block:: python

    from werkzeug.middleware.proxy_fix import ProxyFix

    app.wsgi_app = ProxyFix(
        app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
    )

Remember, only apply this middleware if you are behind a proxy, and set
the correct number of proxies that set each header. It can be a security
issue if you get this configuration wrong.
