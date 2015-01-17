# -*- coding: utf-8 -
#
# This file is part of gunicorn released under the MIT license.
# See the NOTICE for more information.

""" module used to build the django wsgi application """

import os
import re
import sys
import time
try:
    from StringIO import StringIO
except:
    from io import StringIO
    from imp import reload


from django.conf import settings
from django.core.management.validation import get_validation_errors
from django.utils import translation

try:
    from django.core.servers.basehttp import get_internal_wsgi_application
    django14 = True
except ImportError:
    from django.core.handlers.wsgi import WSGIHandler
    django14 = False

from gunicorn import util


def make_wsgi_application():
    # validate models
    s = StringIO()
    if get_validation_errors(s):
        s.seek(0)
        error = s.read()
        sys.stderr.write("One or more models did not validate:\n%s" % error)
        sys.stderr.flush()

        sys.exit(1)

    translation.activate(settings.LANGUAGE_CODE)
    if django14:
        return get_internal_wsgi_application()
    return WSGIHandler()


def reload_django_settings():
        mod = util.import_module(os.environ['DJANGO_SETTINGS_MODULE'])

        # reload module
        reload(mod)

        # reload settings.
        # USe code from django.settings.Settings module.

        # Settings that should be converted into tuples if they're mistakenly entered
        # as strings.
        tuple_settings = ("INSTALLED_APPS", "TEMPLATE_DIRS")

        for setting in dir(mod):
            if setting == setting.upper():
                setting_value = getattr(mod, setting)
                if setting in tuple_settings and type(setting_value) == str:
                    setting_value = (setting_value,)  # In case the user forgot the comma.
                setattr(settings, setting, setting_value)

        # Expand entries in INSTALLED_APPS like "django.contrib.*" to a list
        # of all those apps.
        new_installed_apps = []
        for app in settings.INSTALLED_APPS:
            if app.endswith('.*'):
                app_mod = util.import_module(app[:-2])
                appdir = os.path.dirname(app_mod.__file__)
                app_subdirs = os.listdir(appdir)
                name_pattern = re.compile(r'[a-zA-Z]\w*')
                for d in sorted(app_subdirs):
                    if (name_pattern.match(d) and
                            os.path.isdir(os.path.join(appdir, d))):
                        new_installed_apps.append('%s.%s' % (app[:-2], d))
            else:
                new_installed_apps.append(app)
        setattr(settings, "INSTALLED_APPS", new_installed_apps)

        if hasattr(time, 'tzset') and settings.TIME_ZONE:
            # When we can, attempt to validate the timezone. If we can't find
            # this file, no check happens and it's harmless.
            zoneinfo_root = '/usr/share/zoneinfo'
            if (os.path.exists(zoneinfo_root) and not
                    os.path.exists(os.path.join(zoneinfo_root,
                        *(settings.TIME_ZONE.split('/'))))):
                raise ValueError("Incorrect timezone setting: %s" %
                        settings.TIME_ZONE)
            # Move the time zone info into os.environ. See ticket #2315 for why
            # we don't do this unconditionally (breaks Windows).
            os.environ['TZ'] = settings.TIME_ZONE
            time.tzset()

        # Settings are configured, so we can set up the logger if required
        if getattr(settings, 'LOGGING_CONFIG', False):
            # First find the logging configuration function ...
            logging_config_path, logging_config_func_name = settings.LOGGING_CONFIG.rsplit('.', 1)
            logging_config_module = util.import_module(logging_config_path)
            logging_config_func = getattr(logging_config_module, logging_config_func_name)

            # ... then invoke it with the logging settings
            logging_config_func(settings.LOGGING)


def make_command_wsgi_application(admin_mediapath):
    reload_django_settings()

    try:
        from django.core.servers.basehttp import AdminMediaHandler
        return AdminMediaHandler(make_wsgi_application(), admin_mediapath)
    except ImportError:
        return make_wsgi_application()
