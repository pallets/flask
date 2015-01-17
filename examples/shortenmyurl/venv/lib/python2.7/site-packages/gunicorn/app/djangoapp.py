# -*- coding: utf-8 -
#
# This file is part of gunicorn released under the MIT license.
# See the NOTICE for more information.

import os
import sys

from gunicorn.app.base import Application
from gunicorn import util


def is_setting_mod(path):
    return (os.path.isfile(os.path.join(path, "settings.py")) or
            os.path.isfile(os.path.join(path, "settings.pyc")))


def find_settings_module(path):
    path = os.path.abspath(path)
    project_path = None
    settings_name = "settings"

    if os.path.isdir(path):
        project_path = None
        if not is_setting_mod(path):
            for d in os.listdir(path):
                if d in ('..', '.'):
                    continue

                root = os.path.join(path, d)
                if is_setting_mod(root):
                    project_path = root
                    break
        else:
            project_path = path
    elif os.path.isfile(path):
        project_path = os.path.dirname(path)
        settings_name, _ = os.path.splitext(os.path.basename(path))

    return project_path, settings_name


def make_default_env(cfg):
    if cfg.django_settings:
        os.environ['DJANGO_SETTINGS_MODULE'] = cfg.django_settings

    if cfg.pythonpath and cfg.pythonpath is not None:
        paths = cfg.pythonpath.split(",")
        for path in paths:
            pythonpath = os.path.abspath(cfg.pythonpath)
            if pythonpath not in sys.path:
                sys.path.insert(0, pythonpath)

    try:
        os.environ['DJANGO_SETTINGS_MODULE']
    except KeyError:
        # not settings env set, try to build one.
        cwd = util.getcwd()
        project_path, settings_name = find_settings_module(cwd)

        if not project_path:
            raise RuntimeError("django project not found")

        pythonpath, project_name = os.path.split(project_path)
        os.environ['DJANGO_SETTINGS_MODULE'] = "%s.%s" % (project_name,
                settings_name)
        if pythonpath not in sys.path:
            sys.path.insert(0, pythonpath)

        if project_path not in sys.path:
            sys.path.insert(0, project_path)


class DjangoApplication(Application):

    def init(self, parser, opts, args):
        if args:
            if ("." in args[0] and not (os.path.isfile(args[0])
                    or os.path.isdir(args[0]))):
                self.cfg.set("django_settings", args[0])
            else:
                # not settings env set, try to build one.
                project_path, settings_name = find_settings_module(
                        os.path.abspath(args[0]))
                if project_path not in sys.path:
                    sys.path.insert(0, project_path)

                if not project_path:
                    raise RuntimeError("django project not found")

                pythonpath, project_name = os.path.split(project_path)
                self.cfg.set("django_settings", "%s.%s" % (project_name,
                        settings_name))
                self.cfg.set("pythonpath", pythonpath)

    def load(self):
        # chdir to the configured path before loading,
        # default is the current dir
        os.chdir(self.cfg.chdir)

        # set settings
        make_default_env(self.cfg)

        # load wsgi application and return it.
        mod = util.import_module("gunicorn.app.django_wsgi")
        return mod.make_wsgi_application()


class DjangoApplicationCommand(Application):

    def __init__(self, options, admin_media_path):
        self.usage = None
        self.prog = None
        self.cfg = None
        self.config_file = options.get("config") or ""
        self.options = options
        self.admin_media_path = admin_media_path
        self.callable = None
        self.project_path = None
        self.do_load_config()

    def init(self, *args):
        if 'settings' in self.options:
            self.options['django_settings'] = self.options.pop('settings')

        cfg = {}
        for k, v in self.options.items():
            if k.lower() in self.cfg.settings and v is not None:
                cfg[k.lower()] = v
        return cfg

    def load(self):
        # chdir to the configured path before loading,
        # default is the current dir
        os.chdir(self.cfg.chdir)

        # set settings
        make_default_env(self.cfg)

        # load wsgi application and return it.
        mod = util.import_module("gunicorn.app.django_wsgi")
        return mod.make_command_wsgi_application(self.admin_media_path)


def run():
    """\
    The ``gunicorn_django`` command line runner for launching Django
    applications.
    """
    util.warn("""This command is deprecated.

    You should now run your application with the WSGI interface
    installed with your project. Ex.:

        gunicorn myproject.wsgi:application

    See https://docs.djangoproject.com/en/1.5/howto/deployment/wsgi/gunicorn/
    for more info.""")
    from gunicorn.app.djangoapp import DjangoApplication
    DjangoApplication("%(prog)s [OPTIONS] [SETTINGS_PATH]").run()
