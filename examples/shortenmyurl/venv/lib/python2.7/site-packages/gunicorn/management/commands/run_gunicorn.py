# -*- coding: utf-8 -
#
# This file is part of gunicorn released under the MIT license.
# See the NOTICE for more information.

from optparse import make_option
import sys

from django.core.management.base import BaseCommand, CommandError

from gunicorn.app.djangoapp import DjangoApplicationCommand
from gunicorn.config import make_settings
from gunicorn import util


# monkey patch django.
# This patch make sure that we use real threads to get the ident which
# is going to happen if we are using gevent or eventlet.
try:
    from django.db.backends import BaseDatabaseWrapper, DatabaseError

    if "validate_thread_sharing" in BaseDatabaseWrapper.__dict__:
        import thread
        _get_ident = thread.get_ident

        __old__init__ = BaseDatabaseWrapper.__init__

        def _init(self, *args, **kwargs):
            __old__init__(self, *args, **kwargs)
            self._thread_ident = _get_ident()

        def _validate_thread_sharing(self):
            if (not self.allow_thread_sharing
                and self._thread_ident != _get_ident()):
                    raise DatabaseError("DatabaseWrapper objects created in a "
                        "thread can only be used in that same thread. The object "
                        "with alias '%s' was created in thread id %s and this is "
                        "thread id %s."
                        % (self.alias, self._thread_ident, _get_ident()))

        BaseDatabaseWrapper.__init__ = _init
        BaseDatabaseWrapper.validate_thread_sharing = _validate_thread_sharing
except ImportError:
    pass


def make_options():
    opts = [
        make_option('--adminmedia', dest='admin_media_path', default='',
        help='Specifies the directory from which to serve admin media.')
    ]

    g_settings = make_settings(ignore=("version"))
    keys = g_settings.keys()
    for k in keys:
        if k in ('pythonpath', 'django_settings',):
            continue

        setting = g_settings[k]
        if not setting.cli:
            continue

        args = tuple(setting.cli)

        kwargs = {
            "dest": setting.name,
            "metavar": setting.meta or None,
            "action": setting.action or "store",
            "type": setting.type or "string",
            "default": None,
            "help": "%s [%s]" % (setting.short, setting.default)
        }
        if kwargs["action"] != "store":
            kwargs.pop("type")

        opts.append(make_option(*args, **kwargs))

    return tuple(opts)

GUNICORN_OPTIONS = make_options()


class Command(BaseCommand):
    option_list = BaseCommand.option_list + GUNICORN_OPTIONS
    help = "Starts a fully-functional Web server using gunicorn."
    args = '[optional port number, or ipaddr:port or unix:/path/to/sockfile]'

    # Validation is called explicitly each time the server is reloaded.
    requires_model_validation = False

    def handle(self, addrport=None, *args, **options):

        # deprecation warning to announce future deletion in R21
        util.warn("""This command is deprecated.

        You should now run your application with the WSGI interface
        installed with your project. Ex.:

            gunicorn myproject.wsgi:application

        See https://docs.djangoproject.com/en/1.5/howto/deployment/wsgi/gunicorn/
        for more info.""")

        if args:
            raise CommandError('Usage is run_gunicorn %s' % self.args)

        if addrport:
            sys.argv = sys.argv[:-1]
            options['bind'] = addrport

        admin_media_path = options.pop('admin_media_path', '')

        DjangoApplicationCommand(options, admin_media_path).run()
