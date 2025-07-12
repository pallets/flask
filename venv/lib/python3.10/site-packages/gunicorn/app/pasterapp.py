#
# This file is part of gunicorn released under the MIT license.
# See the NOTICE for more information.

import configparser
import os

from paste.deploy import loadapp

from gunicorn.app.wsgiapp import WSGIApplication
from gunicorn.config import get_default_config_file


def get_wsgi_app(config_uri, name=None, defaults=None):
    if ':' not in config_uri:
        config_uri = "config:%s" % config_uri

    return loadapp(
        config_uri,
        name=name,
        relative_to=os.getcwd(),
        global_conf=defaults,
    )


def has_logging_config(config_file):
    parser = configparser.ConfigParser()
    parser.read([config_file])
    return parser.has_section('loggers')


def serve(app, global_conf, **local_conf):
    """\
    A Paste Deployment server runner.

    Example configuration:

        [server:main]
        use = egg:gunicorn#main
        host = 127.0.0.1
        port = 5000
    """
    config_file = global_conf['__file__']
    gunicorn_config_file = local_conf.pop('config', None)

    host = local_conf.pop('host', '')
    port = local_conf.pop('port', '')
    if host and port:
        local_conf['bind'] = '%s:%s' % (host, port)
    elif host:
        local_conf['bind'] = host.split(',')

    class PasterServerApplication(WSGIApplication):
        def load_config(self):
            self.cfg.set("default_proc_name", config_file)

            if has_logging_config(config_file):
                self.cfg.set("logconfig", config_file)

            if gunicorn_config_file:
                self.load_config_from_file(gunicorn_config_file)
            else:
                default_gunicorn_config_file = get_default_config_file()
                if default_gunicorn_config_file is not None:
                    self.load_config_from_file(default_gunicorn_config_file)

            for k, v in local_conf.items():
                if v is not None:
                    self.cfg.set(k.lower(), v)

        def load(self):
            return app

    PasterServerApplication().run()
