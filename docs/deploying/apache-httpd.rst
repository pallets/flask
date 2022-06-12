Apache httpd
============

`Apache httpd`_ is a fast, production level HTTP server. When serving
your application with one of the WSGI servers listed in :doc:`index`, it
is often good or necessary to put a dedicated HTTP server in front of
it. This "reverse proxy" can handle incoming requests, TLS, and other
security and performance concerns better than the WSGI server.

httpd can be installed using your system package manager, or a pre-built
executable for Windows. Installing and running httpd itself is outside
the scope of this doc. This page outlines the basics of configuring
httpd to proxy your application. Be sure to read its documentation to
understand what features are available.

.. _Apache httpd: https://httpd.apache.org/


Domain Name
-----------

Acquiring and configuring a domain name is outside the scope of this
doc. In general, you will buy a domain name from a registrar, pay for
server space with a hosting provider, and then point your registrar
at the hosting provider's name servers.

To simulate this, you can also edit your ``hosts`` file, located at
``/etc/hosts`` on Linux. Add a line that associates a name with the
local IP.

Modern Linux systems may be configured to treat any domain name that
ends with ``.localhost`` like this without adding it to the ``hosts``
file.

.. code-block:: python
    :caption: ``/etc/hosts``

    127.0.0.1 hello.localhost


Configuration
-------------

The httpd configuration is located at ``/etc/httpd/conf/httpd.conf`` on
Linux. It may be different depending on your operating system. Check the
docs and look for ``httpd.conf``.

Remove or comment out any existing ``DocumentRoot`` directive. Add the
config lines below. We'll assume the WSGI server is listening locally at
``http://127.0.0.1:8000``.

.. code-block:: apache
    :caption: ``/etc/httpd/conf/httpd.conf``

    LoadModule proxy_module modules/mod_proxy.so
    LoadModule proxy_http_module modules/mod_proxy_http.so
    ProxyPass / http://127.0.0.1:8000/
    RequestHeader set X-Forwarded-Proto http
    RequestHeader set X-Forwarded-Prefix /

The ``LoadModule`` lines might already exist. If so, make sure they are
uncommented instead of adding them manually.

Then :doc:`proxy_fix` so that your application uses the ``X-Forwarded``
headers. ``X-Forwarded-For`` and ``X-Forwarded-Host`` are automatically
set by ``ProxyPass``.
