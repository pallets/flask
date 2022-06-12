nginx
=====

`nginx`_ is a fast, production level HTTP server. When serving your
application with one of the WSGI servers listed in :doc:`index`, it is
often good or necessary to put a dedicated HTTP server in front of it.
This "reverse proxy" can handle incoming requests, TLS, and other
security and performance concerns better than the WSGI server.

Nginx can be installed using your system package manager, or a pre-built
executable for Windows. Installing and running Nginx itself is outside
the scope of this doc. This page outlines the basics of configuring
Nginx to proxy your application. Be sure to read its documentation to
understand what features are available.

.. _nginx: https://nginx.org/


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

The nginx configuration is located at ``/etc/nginx/nginx.conf`` on
Linux. It may be different depending on your operating system. Check the
docs and look for ``nginx.conf``.

Remove or comment out any existing ``server`` section. Add a ``server``
section and use the ``proxy_pass`` directive to point to the address the
WSGI server is listening on. We'll assume the WSGI server is listening
locally at ``http://127.0.0.1:8000``.

.. code-block:: nginx
    :caption: ``/etc/nginx.conf``

    server {
        listen 80;
        server_name _;

        location / {
            proxy_pass http://127.0.0.1:8000/;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-Host $host;
            proxy_set_header X-Forwarded-Prefix /;
        }
    }

Then :doc:`proxy_fix` so that your application uses these headers.
