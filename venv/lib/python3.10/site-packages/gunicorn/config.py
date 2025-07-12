#
# This file is part of gunicorn released under the MIT license.
# See the NOTICE for more information.

# Please remember to run "make -C docs html" after update "desc" attributes.

import argparse
import copy
import grp
import inspect
import ipaddress
import os
import pwd
import re
import shlex
import ssl
import sys
import textwrap

from gunicorn import __version__, util
from gunicorn.errors import ConfigError
from gunicorn.reloader import reloader_engines

KNOWN_SETTINGS = []
PLATFORM = sys.platform


def make_settings(ignore=None):
    settings = {}
    ignore = ignore or ()
    for s in KNOWN_SETTINGS:
        setting = s()
        if setting.name in ignore:
            continue
        settings[setting.name] = setting.copy()
    return settings


def auto_int(_, x):
    # for compatible with octal numbers in python3
    if re.match(r'0(\d)', x, re.IGNORECASE):
        x = x.replace('0', '0o', 1)
    return int(x, 0)


class Config:

    def __init__(self, usage=None, prog=None):
        self.settings = make_settings()
        self.usage = usage
        self.prog = prog or os.path.basename(sys.argv[0])
        self.env_orig = os.environ.copy()

    def __str__(self):
        lines = []
        kmax = max(len(k) for k in self.settings)
        for k in sorted(self.settings):
            v = self.settings[k].value
            if callable(v):
                v = "<{}()>".format(v.__qualname__)
            lines.append("{k:{kmax}} = {v}".format(k=k, v=v, kmax=kmax))
        return "\n".join(lines)

    def __getattr__(self, name):
        if name not in self.settings:
            raise AttributeError("No configuration setting for: %s" % name)
        return self.settings[name].get()

    def __setattr__(self, name, value):
        if name != "settings" and name in self.settings:
            raise AttributeError("Invalid access!")
        super().__setattr__(name, value)

    def set(self, name, value):
        if name not in self.settings:
            raise AttributeError("No configuration setting for: %s" % name)
        self.settings[name].set(value)

    def get_cmd_args_from_env(self):
        if 'GUNICORN_CMD_ARGS' in self.env_orig:
            return shlex.split(self.env_orig['GUNICORN_CMD_ARGS'])
        return []

    def parser(self):
        kwargs = {
            "usage": self.usage,
            "prog": self.prog
        }
        parser = argparse.ArgumentParser(**kwargs)
        parser.add_argument("-v", "--version",
                            action="version", default=argparse.SUPPRESS,
                            version="%(prog)s (version " + __version__ + ")\n",
                            help="show program's version number and exit")
        parser.add_argument("args", nargs="*", help=argparse.SUPPRESS)

        keys = sorted(self.settings, key=self.settings.__getitem__)
        for k in keys:
            self.settings[k].add_option(parser)

        return parser

    @property
    def worker_class_str(self):
        uri = self.settings['worker_class'].get()

        if isinstance(uri, str):
            # are we using a threaded worker?
            is_sync = uri.endswith('SyncWorker') or uri == 'sync'
            if is_sync and self.threads > 1:
                return "gthread"
            return uri
        return uri.__name__

    @property
    def worker_class(self):
        uri = self.settings['worker_class'].get()

        # are we using a threaded worker?
        is_sync = isinstance(uri, str) and (uri.endswith('SyncWorker') or uri == 'sync')
        if is_sync and self.threads > 1:
            uri = "gunicorn.workers.gthread.ThreadWorker"

        worker_class = util.load_class(uri)
        if hasattr(worker_class, "setup"):
            worker_class.setup()
        return worker_class

    @property
    def address(self):
        s = self.settings['bind'].get()
        return [util.parse_address(util.bytes_to_str(bind)) for bind in s]

    @property
    def uid(self):
        return self.settings['user'].get()

    @property
    def gid(self):
        return self.settings['group'].get()

    @property
    def proc_name(self):
        pn = self.settings['proc_name'].get()
        if pn is not None:
            return pn
        else:
            return self.settings['default_proc_name'].get()

    @property
    def logger_class(self):
        uri = self.settings['logger_class'].get()
        if uri == "simple":
            # support the default
            uri = LoggerClass.default

        # if default logger is in use, and statsd is on, automagically switch
        # to the statsd logger
        if uri == LoggerClass.default:
            if 'statsd_host' in self.settings and self.settings['statsd_host'].value is not None:
                uri = "gunicorn.instrument.statsd.Statsd"

        logger_class = util.load_class(
            uri,
            default="gunicorn.glogging.Logger",
            section="gunicorn.loggers")

        if hasattr(logger_class, "install"):
            logger_class.install()
        return logger_class

    @property
    def is_ssl(self):
        return self.certfile or self.keyfile

    @property
    def ssl_options(self):
        opts = {}
        for name, value in self.settings.items():
            if value.section == 'SSL':
                opts[name] = value.get()
        return opts

    @property
    def env(self):
        raw_env = self.settings['raw_env'].get()
        env = {}

        if not raw_env:
            return env

        for e in raw_env:
            s = util.bytes_to_str(e)
            try:
                k, v = s.split('=', 1)
            except ValueError:
                raise RuntimeError("environment setting %r invalid" % s)

            env[k] = v

        return env

    @property
    def sendfile(self):
        if self.settings['sendfile'].get() is not None:
            return False

        if 'SENDFILE' in os.environ:
            sendfile = os.environ['SENDFILE'].lower()
            return sendfile in ['y', '1', 'yes', 'true']

        return True

    @property
    def reuse_port(self):
        return self.settings['reuse_port'].get()

    @property
    def paste_global_conf(self):
        raw_global_conf = self.settings['raw_paste_global_conf'].get()
        if raw_global_conf is None:
            return None

        global_conf = {}
        for e in raw_global_conf:
            s = util.bytes_to_str(e)
            try:
                k, v = re.split(r'(?<!\\)=', s, 1)
            except ValueError:
                raise RuntimeError("environment setting %r invalid" % s)
            k = k.replace('\\=', '=')
            v = v.replace('\\=', '=')
            global_conf[k] = v

        return global_conf


class SettingMeta(type):
    def __new__(cls, name, bases, attrs):
        super_new = super().__new__
        parents = [b for b in bases if isinstance(b, SettingMeta)]
        if not parents:
            return super_new(cls, name, bases, attrs)

        attrs["order"] = len(KNOWN_SETTINGS)
        attrs["validator"] = staticmethod(attrs["validator"])

        new_class = super_new(cls, name, bases, attrs)
        new_class.fmt_desc(attrs.get("desc", ""))
        KNOWN_SETTINGS.append(new_class)
        return new_class

    def fmt_desc(cls, desc):
        desc = textwrap.dedent(desc).strip()
        setattr(cls, "desc", desc)
        setattr(cls, "short", desc.splitlines()[0])


class Setting:
    name = None
    value = None
    section = None
    cli = None
    validator = None
    type = None
    meta = None
    action = None
    default = None
    short = None
    desc = None
    nargs = None
    const = None

    def __init__(self):
        if self.default is not None:
            self.set(self.default)

    def add_option(self, parser):
        if not self.cli:
            return
        args = tuple(self.cli)

        help_txt = "%s [%s]" % (self.short, self.default)
        help_txt = help_txt.replace("%", "%%")

        kwargs = {
            "dest": self.name,
            "action": self.action or "store",
            "type": self.type or str,
            "default": None,
            "help": help_txt
        }

        if self.meta is not None:
            kwargs['metavar'] = self.meta

        if kwargs["action"] != "store":
            kwargs.pop("type")

        if self.nargs is not None:
            kwargs["nargs"] = self.nargs

        if self.const is not None:
            kwargs["const"] = self.const

        parser.add_argument(*args, **kwargs)

    def copy(self):
        return copy.copy(self)

    def get(self):
        return self.value

    def set(self, val):
        if not callable(self.validator):
            raise TypeError('Invalid validator: %s' % self.name)
        self.value = self.validator(val)

    def __lt__(self, other):
        return (self.section == other.section and
                self.order < other.order)
    __cmp__ = __lt__

    def __repr__(self):
        return "<%s.%s object at %x with value %r>" % (
            self.__class__.__module__,
            self.__class__.__name__,
            id(self),
            self.value,
        )


Setting = SettingMeta('Setting', (Setting,), {})


def validate_bool(val):
    if val is None:
        return

    if isinstance(val, bool):
        return val
    if not isinstance(val, str):
        raise TypeError("Invalid type for casting: %s" % val)
    if val.lower().strip() == "true":
        return True
    elif val.lower().strip() == "false":
        return False
    else:
        raise ValueError("Invalid boolean: %s" % val)


def validate_dict(val):
    if not isinstance(val, dict):
        raise TypeError("Value is not a dictionary: %s " % val)
    return val


def validate_pos_int(val):
    if not isinstance(val, int):
        val = int(val, 0)
    else:
        # Booleans are ints!
        val = int(val)
    if val < 0:
        raise ValueError("Value must be positive: %s" % val)
    return val


def validate_ssl_version(val):
    if val != SSLVersion.default:
        sys.stderr.write("Warning: option `ssl_version` is deprecated and it is ignored. Use ssl_context instead.\n")
    return val


def validate_string(val):
    if val is None:
        return None
    if not isinstance(val, str):
        raise TypeError("Not a string: %s" % val)
    return val.strip()


def validate_file_exists(val):
    if val is None:
        return None
    if not os.path.exists(val):
        raise ValueError("File %s does not exists." % val)
    return val


def validate_list_string(val):
    if not val:
        return []

    # legacy syntax
    if isinstance(val, str):
        val = [val]

    return [validate_string(v) for v in val]


def validate_list_of_existing_files(val):
    return [validate_file_exists(v) for v in validate_list_string(val)]


def validate_string_to_addr_list(val):
    val = validate_string_to_list(val)

    for addr in val:
        if addr == "*":
            continue
        _vaid_ip = ipaddress.ip_address(addr)

    return val


def validate_string_to_list(val):
    val = validate_string(val)

    if not val:
        return []

    return [v.strip() for v in val.split(",") if v]


def validate_class(val):
    if inspect.isfunction(val) or inspect.ismethod(val):
        val = val()
    if inspect.isclass(val):
        return val
    return validate_string(val)


def validate_callable(arity):
    def _validate_callable(val):
        if isinstance(val, str):
            try:
                mod_name, obj_name = val.rsplit(".", 1)
            except ValueError:
                raise TypeError("Value '%s' is not import string. "
                                "Format: module[.submodules...].object" % val)
            try:
                mod = __import__(mod_name, fromlist=[obj_name])
                val = getattr(mod, obj_name)
            except ImportError as e:
                raise TypeError(str(e))
            except AttributeError:
                raise TypeError("Can not load '%s' from '%s'"
                                "" % (obj_name, mod_name))
        if not callable(val):
            raise TypeError("Value is not callable: %s" % val)
        if arity != -1 and arity != util.get_arity(val):
            raise TypeError("Value must have an arity of: %s" % arity)
        return val
    return _validate_callable


def validate_user(val):
    if val is None:
        return os.geteuid()
    if isinstance(val, int):
        return val
    elif val.isdigit():
        return int(val)
    else:
        try:
            return pwd.getpwnam(val).pw_uid
        except KeyError:
            raise ConfigError("No such user: '%s'" % val)


def validate_group(val):
    if val is None:
        return os.getegid()

    if isinstance(val, int):
        return val
    elif val.isdigit():
        return int(val)
    else:
        try:
            return grp.getgrnam(val).gr_gid
        except KeyError:
            raise ConfigError("No such group: '%s'" % val)


def validate_post_request(val):
    val = validate_callable(-1)(val)

    largs = util.get_arity(val)
    if largs == 4:
        return val
    elif largs == 3:
        return lambda worker, req, env, _r: val(worker, req, env)
    elif largs == 2:
        return lambda worker, req, _e, _r: val(worker, req)
    else:
        raise TypeError("Value must have an arity of: 4")


def validate_chdir(val):
    # valid if the value is a string
    val = validate_string(val)

    # transform relative paths
    path = os.path.abspath(os.path.normpath(os.path.join(util.getcwd(), val)))

    # test if the path exists
    if not os.path.exists(path):
        raise ConfigError("can't chdir to %r" % val)

    return path


def validate_statsd_address(val):
    val = validate_string(val)
    if val is None:
        return None

    # As of major release 20, util.parse_address would recognize unix:PORT
    # as a UDS address, breaking backwards compatibility. We defend against
    # that regression here (this is also unit-tested).
    # Feel free to remove in the next major release.
    unix_hostname_regression = re.match(r'^unix:(\d+)$', val)
    if unix_hostname_regression:
        return ('unix', int(unix_hostname_regression.group(1)))

    try:
        address = util.parse_address(val, default_port='8125')
    except RuntimeError:
        raise TypeError("Value must be one of ('host:port', 'unix://PATH')")

    return address


def validate_reload_engine(val):
    if val not in reloader_engines:
        raise ConfigError("Invalid reload_engine: %r" % val)

    return val


def get_default_config_file():
    config_path = os.path.join(os.path.abspath(os.getcwd()),
                               'gunicorn.conf.py')
    if os.path.exists(config_path):
        return config_path
    return None


class ConfigFile(Setting):
    name = "config"
    section = "Config File"
    cli = ["-c", "--config"]
    meta = "CONFIG"
    validator = validate_string
    default = "./gunicorn.conf.py"
    desc = """\
        :ref:`The Gunicorn config file<configuration_file>`.

        A string of the form ``PATH``, ``file:PATH``, or ``python:MODULE_NAME``.

        Only has an effect when specified on the command line or as part of an
        application specific configuration.

        By default, a file named ``gunicorn.conf.py`` will be read from the same
        directory where gunicorn is being run.

        .. versionchanged:: 19.4
           Loading the config from a Python module requires the ``python:``
           prefix.
        """


class WSGIApp(Setting):
    name = "wsgi_app"
    section = "Config File"
    meta = "STRING"
    validator = validate_string
    default = None
    desc = """\
        A WSGI application path in pattern ``$(MODULE_NAME):$(VARIABLE_NAME)``.

        .. versionadded:: 20.1.0
        """


class Bind(Setting):
    name = "bind"
    action = "append"
    section = "Server Socket"
    cli = ["-b", "--bind"]
    meta = "ADDRESS"
    validator = validate_list_string

    if 'PORT' in os.environ:
        default = ['0.0.0.0:{0}'.format(os.environ.get('PORT'))]
    else:
        default = ['127.0.0.1:8000']

    desc = """\
        The socket to bind.

        A string of the form: ``HOST``, ``HOST:PORT``, ``unix:PATH``,
        ``fd://FD``. An IP is a valid ``HOST``.

        .. versionchanged:: 20.0
           Support for ``fd://FD`` got added.

        Multiple addresses can be bound. ex.::

            $ gunicorn -b 127.0.0.1:8000 -b [::1]:8000 test:app

        will bind the `test:app` application on localhost both on ipv6
        and ipv4 interfaces.

        If the ``PORT`` environment variable is defined, the default
        is ``['0.0.0.0:$PORT']``. If it is not defined, the default
        is ``['127.0.0.1:8000']``.
        """


class Backlog(Setting):
    name = "backlog"
    section = "Server Socket"
    cli = ["--backlog"]
    meta = "INT"
    validator = validate_pos_int
    type = int
    default = 2048
    desc = """\
        The maximum number of pending connections.

        This refers to the number of clients that can be waiting to be served.
        Exceeding this number results in the client getting an error when
        attempting to connect. It should only affect servers under significant
        load.

        Must be a positive integer. Generally set in the 64-2048 range.
        """


class Workers(Setting):
    name = "workers"
    section = "Worker Processes"
    cli = ["-w", "--workers"]
    meta = "INT"
    validator = validate_pos_int
    type = int
    default = int(os.environ.get("WEB_CONCURRENCY", 1))
    desc = """\
        The number of worker processes for handling requests.

        A positive integer generally in the ``2-4 x $(NUM_CORES)`` range.
        You'll want to vary this a bit to find the best for your particular
        application's work load.

        By default, the value of the ``WEB_CONCURRENCY`` environment variable,
        which is set by some Platform-as-a-Service providers such as Heroku. If
        it is not defined, the default is ``1``.
        """


class WorkerClass(Setting):
    name = "worker_class"
    section = "Worker Processes"
    cli = ["-k", "--worker-class"]
    meta = "STRING"
    validator = validate_class
    default = "sync"
    desc = """\
        The type of workers to use.

        The default class (``sync``) should handle most "normal" types of
        workloads. You'll want to read :doc:`design` for information on when
        you might want to choose one of the other worker classes. Required
        libraries may be installed using setuptools' ``extras_require`` feature.

        A string referring to one of the following bundled classes:

        * ``sync``
        * ``eventlet`` - Requires eventlet >= 0.24.1 (or install it via
          ``pip install gunicorn[eventlet]``)
        * ``gevent``   - Requires gevent >= 1.4 (or install it via
          ``pip install gunicorn[gevent]``)
        * ``tornado``  - Requires tornado >= 0.2 (or install it via
          ``pip install gunicorn[tornado]``)
        * ``gthread``  - Python 2 requires the futures package to be installed
          (or install it via ``pip install gunicorn[gthread]``)

        Optionally, you can provide your own worker by giving Gunicorn a
        Python path to a subclass of ``gunicorn.workers.base.Worker``.
        This alternative syntax will load the gevent class:
        ``gunicorn.workers.ggevent.GeventWorker``.
        """


class WorkerThreads(Setting):
    name = "threads"
    section = "Worker Processes"
    cli = ["--threads"]
    meta = "INT"
    validator = validate_pos_int
    type = int
    default = 1
    desc = """\
        The number of worker threads for handling requests.

        Run each worker with the specified number of threads.

        A positive integer generally in the ``2-4 x $(NUM_CORES)`` range.
        You'll want to vary this a bit to find the best for your particular
        application's work load.

        If it is not defined, the default is ``1``.

        This setting only affects the Gthread worker type.

        .. note::
           If you try to use the ``sync`` worker type and set the ``threads``
           setting to more than 1, the ``gthread`` worker type will be used
           instead.
        """


class WorkerConnections(Setting):
    name = "worker_connections"
    section = "Worker Processes"
    cli = ["--worker-connections"]
    meta = "INT"
    validator = validate_pos_int
    type = int
    default = 1000
    desc = """\
        The maximum number of simultaneous clients.

        This setting only affects the ``gthread``, ``eventlet`` and ``gevent`` worker types.
        """


class MaxRequests(Setting):
    name = "max_requests"
    section = "Worker Processes"
    cli = ["--max-requests"]
    meta = "INT"
    validator = validate_pos_int
    type = int
    default = 0
    desc = """\
        The maximum number of requests a worker will process before restarting.

        Any value greater than zero will limit the number of requests a worker
        will process before automatically restarting. This is a simple method
        to help limit the damage of memory leaks.

        If this is set to zero (the default) then the automatic worker
        restarts are disabled.
        """


class MaxRequestsJitter(Setting):
    name = "max_requests_jitter"
    section = "Worker Processes"
    cli = ["--max-requests-jitter"]
    meta = "INT"
    validator = validate_pos_int
    type = int
    default = 0
    desc = """\
        The maximum jitter to add to the *max_requests* setting.

        The jitter causes the restart per worker to be randomized by
        ``randint(0, max_requests_jitter)``. This is intended to stagger worker
        restarts to avoid all workers restarting at the same time.

        .. versionadded:: 19.2
        """


class Timeout(Setting):
    name = "timeout"
    section = "Worker Processes"
    cli = ["-t", "--timeout"]
    meta = "INT"
    validator = validate_pos_int
    type = int
    default = 30
    desc = """\
        Workers silent for more than this many seconds are killed and restarted.

        Value is a positive number or 0. Setting it to 0 has the effect of
        infinite timeouts by disabling timeouts for all workers entirely.

        Generally, the default of thirty seconds should suffice. Only set this
        noticeably higher if you're sure of the repercussions for sync workers.
        For the non sync workers it just means that the worker process is still
        communicating and is not tied to the length of time required to handle a
        single request.
        """


class GracefulTimeout(Setting):
    name = "graceful_timeout"
    section = "Worker Processes"
    cli = ["--graceful-timeout"]
    meta = "INT"
    validator = validate_pos_int
    type = int
    default = 30
    desc = """\
        Timeout for graceful workers restart.

        After receiving a restart signal, workers have this much time to finish
        serving requests. Workers still alive after the timeout (starting from
        the receipt of the restart signal) are force killed.
        """


class Keepalive(Setting):
    name = "keepalive"
    section = "Worker Processes"
    cli = ["--keep-alive"]
    meta = "INT"
    validator = validate_pos_int
    type = int
    default = 2
    desc = """\
        The number of seconds to wait for requests on a Keep-Alive connection.

        Generally set in the 1-5 seconds range for servers with direct connection
        to the client (e.g. when you don't have separate load balancer). When
        Gunicorn is deployed behind a load balancer, it often makes sense to
        set this to a higher value.

        .. note::
           ``sync`` worker does not support persistent connections and will
           ignore this option.
        """


class LimitRequestLine(Setting):
    name = "limit_request_line"
    section = "Security"
    cli = ["--limit-request-line"]
    meta = "INT"
    validator = validate_pos_int
    type = int
    default = 4094
    desc = """\
        The maximum size of HTTP request line in bytes.

        This parameter is used to limit the allowed size of a client's
        HTTP request-line. Since the request-line consists of the HTTP
        method, URI, and protocol version, this directive places a
        restriction on the length of a request-URI allowed for a request
        on the server. A server needs this value to be large enough to
        hold any of its resource names, including any information that
        might be passed in the query part of a GET request. Value is a number
        from 0 (unlimited) to 8190.

        This parameter can be used to prevent any DDOS attack.
        """


class LimitRequestFields(Setting):
    name = "limit_request_fields"
    section = "Security"
    cli = ["--limit-request-fields"]
    meta = "INT"
    validator = validate_pos_int
    type = int
    default = 100
    desc = """\
        Limit the number of HTTP headers fields in a request.

        This parameter is used to limit the number of headers in a request to
        prevent DDOS attack. Used with the *limit_request_field_size* it allows
        more safety. By default this value is 100 and can't be larger than
        32768.
        """


class LimitRequestFieldSize(Setting):
    name = "limit_request_field_size"
    section = "Security"
    cli = ["--limit-request-field_size"]
    meta = "INT"
    validator = validate_pos_int
    type = int
    default = 8190
    desc = """\
        Limit the allowed size of an HTTP request header field.

        Value is a positive number or 0. Setting it to 0 will allow unlimited
        header field sizes.

        .. warning::
           Setting this parameter to a very high or unlimited value can open
           up for DDOS attacks.
        """


class Reload(Setting):
    name = "reload"
    section = 'Debugging'
    cli = ['--reload']
    validator = validate_bool
    action = 'store_true'
    default = False

    desc = '''\
        Restart workers when code changes.

        This setting is intended for development. It will cause workers to be
        restarted whenever application code changes.

        The reloader is incompatible with application preloading. When using a
        paste configuration be sure that the server block does not import any
        application code or the reload will not work as designed.

        The default behavior is to attempt inotify with a fallback to file
        system polling. Generally, inotify should be preferred if available
        because it consumes less system resources.

        .. note::
           In order to use the inotify reloader, you must have the ``inotify``
           package installed.
        '''


class ReloadEngine(Setting):
    name = "reload_engine"
    section = "Debugging"
    cli = ["--reload-engine"]
    meta = "STRING"
    validator = validate_reload_engine
    default = "auto"
    desc = """\
        The implementation that should be used to power :ref:`reload`.

        Valid engines are:

        * ``'auto'``
        * ``'poll'``
        * ``'inotify'`` (requires inotify)

        .. versionadded:: 19.7
        """


class ReloadExtraFiles(Setting):
    name = "reload_extra_files"
    action = "append"
    section = "Debugging"
    cli = ["--reload-extra-file"]
    meta = "FILES"
    validator = validate_list_of_existing_files
    default = []
    desc = """\
        Extends :ref:`reload` option to also watch and reload on additional files
        (e.g., templates, configurations, specifications, etc.).

        .. versionadded:: 19.8
        """


class Spew(Setting):
    name = "spew"
    section = "Debugging"
    cli = ["--spew"]
    validator = validate_bool
    action = "store_true"
    default = False
    desc = """\
        Install a trace function that spews every line executed by the server.

        This is the nuclear option.
        """


class ConfigCheck(Setting):
    name = "check_config"
    section = "Debugging"
    cli = ["--check-config"]
    validator = validate_bool
    action = "store_true"
    default = False
    desc = """\
        Check the configuration and exit. The exit status is 0 if the
        configuration is correct, and 1 if the configuration is incorrect.
        """


class PrintConfig(Setting):
    name = "print_config"
    section = "Debugging"
    cli = ["--print-config"]
    validator = validate_bool
    action = "store_true"
    default = False
    desc = """\
        Print the configuration settings as fully resolved. Implies :ref:`check-config`.
        """


class PreloadApp(Setting):
    name = "preload_app"
    section = "Server Mechanics"
    cli = ["--preload"]
    validator = validate_bool
    action = "store_true"
    default = False
    desc = """\
        Load application code before the worker processes are forked.

        By preloading an application you can save some RAM resources as well as
        speed up server boot times. Although, if you defer application loading
        to each worker process, you can reload your application code easily by
        restarting workers.
        """


class Sendfile(Setting):
    name = "sendfile"
    section = "Server Mechanics"
    cli = ["--no-sendfile"]
    validator = validate_bool
    action = "store_const"
    const = False

    desc = """\
        Disables the use of ``sendfile()``.

        If not set, the value of the ``SENDFILE`` environment variable is used
        to enable or disable its usage.

        .. versionadded:: 19.2
        .. versionchanged:: 19.4
           Swapped ``--sendfile`` with ``--no-sendfile`` to actually allow
           disabling.
        .. versionchanged:: 19.6
           added support for the ``SENDFILE`` environment variable
        """


class ReusePort(Setting):
    name = "reuse_port"
    section = "Server Mechanics"
    cli = ["--reuse-port"]
    validator = validate_bool
    action = "store_true"
    default = False

    desc = """\
        Set the ``SO_REUSEPORT`` flag on the listening socket.

        .. versionadded:: 19.8
        """


class Chdir(Setting):
    name = "chdir"
    section = "Server Mechanics"
    cli = ["--chdir"]
    validator = validate_chdir
    default = util.getcwd()
    default_doc = "``'.'``"
    desc = """\
        Change directory to specified directory before loading apps.
        """


class Daemon(Setting):
    name = "daemon"
    section = "Server Mechanics"
    cli = ["-D", "--daemon"]
    validator = validate_bool
    action = "store_true"
    default = False
    desc = """\
        Daemonize the Gunicorn process.

        Detaches the server from the controlling terminal and enters the
        background.
        """


class Env(Setting):
    name = "raw_env"
    action = "append"
    section = "Server Mechanics"
    cli = ["-e", "--env"]
    meta = "ENV"
    validator = validate_list_string
    default = []

    desc = """\
        Set environment variables in the execution environment.

        Should be a list of strings in the ``key=value`` format.

        For example on the command line:

        .. code-block:: console

            $ gunicorn -b 127.0.0.1:8000 --env FOO=1 test:app

        Or in the configuration file:

        .. code-block:: python

            raw_env = ["FOO=1"]
        """


class Pidfile(Setting):
    name = "pidfile"
    section = "Server Mechanics"
    cli = ["-p", "--pid"]
    meta = "FILE"
    validator = validate_string
    default = None
    desc = """\
        A filename to use for the PID file.

        If not set, no PID file will be written.
        """


class WorkerTmpDir(Setting):
    name = "worker_tmp_dir"
    section = "Server Mechanics"
    cli = ["--worker-tmp-dir"]
    meta = "DIR"
    validator = validate_string
    default = None
    desc = """\
        A directory to use for the worker heartbeat temporary file.

        If not set, the default temporary directory will be used.

        .. note::
           The current heartbeat system involves calling ``os.fchmod`` on
           temporary file handlers and may block a worker for arbitrary time
           if the directory is on a disk-backed filesystem.

           See :ref:`blocking-os-fchmod` for more detailed information
           and a solution for avoiding this problem.
        """


class User(Setting):
    name = "user"
    section = "Server Mechanics"
    cli = ["-u", "--user"]
    meta = "USER"
    validator = validate_user
    default = os.geteuid()
    default_doc = "``os.geteuid()``"
    desc = """\
        Switch worker processes to run as this user.

        A valid user id (as an integer) or the name of a user that can be
        retrieved with a call to ``pwd.getpwnam(value)`` or ``None`` to not
        change the worker process user.
        """


class Group(Setting):
    name = "group"
    section = "Server Mechanics"
    cli = ["-g", "--group"]
    meta = "GROUP"
    validator = validate_group
    default = os.getegid()
    default_doc = "``os.getegid()``"
    desc = """\
        Switch worker process to run as this group.

        A valid group id (as an integer) or the name of a user that can be
        retrieved with a call to ``pwd.getgrnam(value)`` or ``None`` to not
        change the worker processes group.
        """


class Umask(Setting):
    name = "umask"
    section = "Server Mechanics"
    cli = ["-m", "--umask"]
    meta = "INT"
    validator = validate_pos_int
    type = auto_int
    default = 0
    desc = """\
        A bit mask for the file mode on files written by Gunicorn.

        Note that this affects unix socket permissions.

        A valid value for the ``os.umask(mode)`` call or a string compatible
        with ``int(value, 0)`` (``0`` means Python guesses the base, so values
        like ``0``, ``0xFF``, ``0022`` are valid for decimal, hex, and octal
        representations)
        """


class Initgroups(Setting):
    name = "initgroups"
    section = "Server Mechanics"
    cli = ["--initgroups"]
    validator = validate_bool
    action = 'store_true'
    default = False

    desc = """\
        If true, set the worker process's group access list with all of the
        groups of which the specified username is a member, plus the specified
        group id.

        .. versionadded:: 19.7
        """


class TmpUploadDir(Setting):
    name = "tmp_upload_dir"
    section = "Server Mechanics"
    meta = "DIR"
    validator = validate_string
    default = None
    desc = """\
        Directory to store temporary request data as they are read.

        This may disappear in the near future.

        This path should be writable by the process permissions set for Gunicorn
        workers. If not specified, Gunicorn will choose a system generated
        temporary directory.
        """


class SecureSchemeHeader(Setting):
    name = "secure_scheme_headers"
    section = "Server Mechanics"
    validator = validate_dict
    default = {
        "X-FORWARDED-PROTOCOL": "ssl",
        "X-FORWARDED-PROTO": "https",
        "X-FORWARDED-SSL": "on"
    }
    desc = """\

        A dictionary containing headers and values that the front-end proxy
        uses to indicate HTTPS requests. If the source IP is permitted by
        :ref:`forwarded-allow-ips` (below), *and* at least one request header matches
        a key-value pair listed in this dictionary, then Gunicorn will set
        ``wsgi.url_scheme`` to ``https``, so your application can tell that the
        request is secure.

        If the other headers listed in this dictionary are not present in the request, they will be ignored,
        but if the other headers are present and do not match the provided values, then
        the request will fail to parse. See the note below for more detailed examples of this behaviour.

        The dictionary should map upper-case header names to exact string
        values. The value comparisons are case-sensitive, unlike the header
        names, so make sure they're exactly what your front-end proxy sends
        when handling HTTPS requests.

        It is important that your front-end proxy configuration ensures that
        the headers defined here can not be passed directly from the client.
        """


class ForwardedAllowIPS(Setting):
    name = "forwarded_allow_ips"
    section = "Server Mechanics"
    cli = ["--forwarded-allow-ips"]
    meta = "STRING"
    validator = validate_string_to_addr_list
    default = os.environ.get("FORWARDED_ALLOW_IPS", "127.0.0.1,::1")
    desc = """\
        Front-end's IPs from which allowed to handle set secure headers.
        (comma separated).

        Set to ``*`` to disable checking of front-end IPs. This is useful for setups
        where you don't know in advance the IP address of front-end, but
        instead have ensured via other means that only your
        authorized front-ends can access Gunicorn.

        By default, the value of the ``FORWARDED_ALLOW_IPS`` environment
        variable. If it is not defined, the default is ``"127.0.0.1,::1"``.

        .. note::

            This option does not affect UNIX socket connections. Connections not associated with
            an IP address are treated as allowed, unconditionally.

        .. note::

            The interplay between the request headers, the value of ``forwarded_allow_ips``, and the value of
            ``secure_scheme_headers`` is complex. Various scenarios are documented below to further elaborate.
            In each case, we have a request from the remote address 134.213.44.18, and the default value of
            ``secure_scheme_headers``:

            .. code::

                secure_scheme_headers = {
                    'X-FORWARDED-PROTOCOL': 'ssl',
                    'X-FORWARDED-PROTO': 'https',
                    'X-FORWARDED-SSL': 'on'
                }


            .. list-table::
                :header-rows: 1
                :align: center
                :widths: auto

                * - ``forwarded-allow-ips``
                  - Secure Request Headers
                  - Result
                  - Explanation
                * - .. code::

                        ["127.0.0.1"]
                  - .. code::

                        X-Forwarded-Proto: https
                  - .. code::

                        wsgi.url_scheme = "http"
                  - IP address was not allowed
                * - .. code::

                        "*"
                  - <none>
                  - .. code::

                        wsgi.url_scheme = "http"
                  - IP address allowed, but no secure headers provided
                * - .. code::

                        "*"
                  - .. code::

                        X-Forwarded-Proto: https
                  - .. code::

                        wsgi.url_scheme = "https"
                  - IP address allowed, one request header matched
                * - .. code::

                        ["134.213.44.18"]
                  - .. code::

                        X-Forwarded-Ssl: on
                        X-Forwarded-Proto: http
                  - ``InvalidSchemeHeaders()`` raised
                  - IP address allowed, but the two secure headers disagreed on if HTTPS was used


        """


class AccessLog(Setting):
    name = "accesslog"
    section = "Logging"
    cli = ["--access-logfile"]
    meta = "FILE"
    validator = validate_string
    default = None
    desc = """\
        The Access log file to write to.

        ``'-'`` means log to stdout.
        """


class DisableRedirectAccessToSyslog(Setting):
    name = "disable_redirect_access_to_syslog"
    section = "Logging"
    cli = ["--disable-redirect-access-to-syslog"]
    validator = validate_bool
    action = 'store_true'
    default = False
    desc = """\
    Disable redirect access logs to syslog.

    .. versionadded:: 19.8
    """


class AccessLogFormat(Setting):
    name = "access_log_format"
    section = "Logging"
    cli = ["--access-logformat"]
    meta = "STRING"
    validator = validate_string
    default = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
    desc = """\
        The access log format.

        ===========  ===========
        Identifier   Description
        ===========  ===========
        h            remote address
        l            ``'-'``
        u            user name (if HTTP Basic auth used)
        t            date of the request
        r            status line (e.g. ``GET / HTTP/1.1``)
        m            request method
        U            URL path without query string
        q            query string
        H            protocol
        s            status
        B            response length
        b            response length or ``'-'`` (CLF format)
        f            referrer (note: header is ``referer``)
        a            user agent
        T            request time in seconds
        M            request time in milliseconds
        D            request time in microseconds
        L            request time in decimal seconds
        p            process ID
        {header}i    request header
        {header}o    response header
        {variable}e  environment variable
        ===========  ===========

        Use lowercase for header and environment variable names, and put
        ``{...}x`` names inside ``%(...)s``. For example::

            %({x-forwarded-for}i)s
        """


class ErrorLog(Setting):
    name = "errorlog"
    section = "Logging"
    cli = ["--error-logfile", "--log-file"]
    meta = "FILE"
    validator = validate_string
    default = '-'
    desc = """\
        The Error log file to write to.

        Using ``'-'`` for FILE makes gunicorn log to stderr.

        .. versionchanged:: 19.2
           Log to stderr by default.

        """


class Loglevel(Setting):
    name = "loglevel"
    section = "Logging"
    cli = ["--log-level"]
    meta = "LEVEL"
    validator = validate_string
    default = "info"
    desc = """\
        The granularity of Error log outputs.

        Valid level names are:

        * ``'debug'``
        * ``'info'``
        * ``'warning'``
        * ``'error'``
        * ``'critical'``
        """


class CaptureOutput(Setting):
    name = "capture_output"
    section = "Logging"
    cli = ["--capture-output"]
    validator = validate_bool
    action = 'store_true'
    default = False
    desc = """\
        Redirect stdout/stderr to specified file in :ref:`errorlog`.

        .. versionadded:: 19.6
        """


class LoggerClass(Setting):
    name = "logger_class"
    section = "Logging"
    cli = ["--logger-class"]
    meta = "STRING"
    validator = validate_class
    default = "gunicorn.glogging.Logger"
    desc = """\
        The logger you want to use to log events in Gunicorn.

        The default class (``gunicorn.glogging.Logger``) handles most
        normal usages in logging. It provides error and access logging.

        You can provide your own logger by giving Gunicorn a Python path to a
        class that quacks like ``gunicorn.glogging.Logger``.
        """


class LogConfig(Setting):
    name = "logconfig"
    section = "Logging"
    cli = ["--log-config"]
    meta = "FILE"
    validator = validate_string
    default = None
    desc = """\
    The log config file to use.
    Gunicorn uses the standard Python logging module's Configuration
    file format.
    """


class LogConfigDict(Setting):
    name = "logconfig_dict"
    section = "Logging"
    validator = validate_dict
    default = {}
    desc = """\
    The log config dictionary to use, using the standard Python
    logging module's dictionary configuration format. This option
    takes precedence over the :ref:`logconfig` and :ref:`logconfig-json` options,
    which uses the older file configuration format and JSON
    respectively.

    Format: https://docs.python.org/3/library/logging.config.html#logging.config.dictConfig

    For more context you can look at the default configuration dictionary for logging,
    which can be found at ``gunicorn.glogging.CONFIG_DEFAULTS``.

    .. versionadded:: 19.8
    """


class LogConfigJson(Setting):
    name = "logconfig_json"
    section = "Logging"
    cli = ["--log-config-json"]
    meta = "FILE"
    validator = validate_string
    default = None
    desc = """\
    The log config to read config from a JSON file

    Format: https://docs.python.org/3/library/logging.config.html#logging.config.jsonConfig

    .. versionadded:: 20.0
    """


class SyslogTo(Setting):
    name = "syslog_addr"
    section = "Logging"
    cli = ["--log-syslog-to"]
    meta = "SYSLOG_ADDR"
    validator = validate_string

    if PLATFORM == "darwin":
        default = "unix:///var/run/syslog"
    elif PLATFORM in ('freebsd', 'dragonfly', ):
        default = "unix:///var/run/log"
    elif PLATFORM == "openbsd":
        default = "unix:///dev/log"
    else:
        default = "udp://localhost:514"

    desc = """\
    Address to send syslog messages.

    Address is a string of the form:

    * ``unix://PATH#TYPE`` : for unix domain socket. ``TYPE`` can be ``stream``
      for the stream driver or ``dgram`` for the dgram driver.
      ``stream`` is the default.
    * ``udp://HOST:PORT`` : for UDP sockets
    * ``tcp://HOST:PORT`` : for TCP sockets

    """


class Syslog(Setting):
    name = "syslog"
    section = "Logging"
    cli = ["--log-syslog"]
    validator = validate_bool
    action = 'store_true'
    default = False
    desc = """\
    Send *Gunicorn* logs to syslog.

    .. versionchanged:: 19.8
       You can now disable sending access logs by using the
       :ref:`disable-redirect-access-to-syslog` setting.
    """


class SyslogPrefix(Setting):
    name = "syslog_prefix"
    section = "Logging"
    cli = ["--log-syslog-prefix"]
    meta = "SYSLOG_PREFIX"
    validator = validate_string
    default = None
    desc = """\
    Makes Gunicorn use the parameter as program-name in the syslog entries.

    All entries will be prefixed by ``gunicorn.<prefix>``. By default the
    program name is the name of the process.
    """


class SyslogFacility(Setting):
    name = "syslog_facility"
    section = "Logging"
    cli = ["--log-syslog-facility"]
    meta = "SYSLOG_FACILITY"
    validator = validate_string
    default = "user"
    desc = """\
    Syslog facility name
    """


class EnableStdioInheritance(Setting):
    name = "enable_stdio_inheritance"
    section = "Logging"
    cli = ["-R", "--enable-stdio-inheritance"]
    validator = validate_bool
    default = False
    action = "store_true"
    desc = """\
    Enable stdio inheritance.

    Enable inheritance for stdio file descriptors in daemon mode.

    Note: To disable the Python stdout buffering, you can to set the user
    environment variable ``PYTHONUNBUFFERED`` .
    """


# statsD monitoring
class StatsdHost(Setting):
    name = "statsd_host"
    section = "Logging"
    cli = ["--statsd-host"]
    meta = "STATSD_ADDR"
    default = None
    validator = validate_statsd_address
    desc = """\
    The address of the StatsD server to log to.

    Address is a string of the form:

    * ``unix://PATH`` : for a unix domain socket.
    * ``HOST:PORT`` : for a network address

    .. versionadded:: 19.1
    """


# Datadog Statsd (dogstatsd) tags. https://docs.datadoghq.com/developers/dogstatsd/
class DogstatsdTags(Setting):
    name = "dogstatsd_tags"
    section = "Logging"
    cli = ["--dogstatsd-tags"]
    meta = "DOGSTATSD_TAGS"
    default = ""
    validator = validate_string
    desc = """\
    A comma-delimited list of datadog statsd (dogstatsd) tags to append to
    statsd metrics.

    .. versionadded:: 20
    """


class StatsdPrefix(Setting):
    name = "statsd_prefix"
    section = "Logging"
    cli = ["--statsd-prefix"]
    meta = "STATSD_PREFIX"
    default = ""
    validator = validate_string
    desc = """\
    Prefix to use when emitting statsd metrics (a trailing ``.`` is added,
    if not provided).

    .. versionadded:: 19.2
    """


class Procname(Setting):
    name = "proc_name"
    section = "Process Naming"
    cli = ["-n", "--name"]
    meta = "STRING"
    validator = validate_string
    default = None
    desc = """\
        A base to use with setproctitle for process naming.

        This affects things like ``ps`` and ``top``. If you're going to be
        running more than one instance of Gunicorn you'll probably want to set a
        name to tell them apart. This requires that you install the setproctitle
        module.

        If not set, the *default_proc_name* setting will be used.
        """


class DefaultProcName(Setting):
    name = "default_proc_name"
    section = "Process Naming"
    validator = validate_string
    default = "gunicorn"
    desc = """\
        Internal setting that is adjusted for each type of application.
        """


class PythonPath(Setting):
    name = "pythonpath"
    section = "Server Mechanics"
    cli = ["--pythonpath"]
    meta = "STRING"
    validator = validate_string
    default = None
    desc = """\
        A comma-separated list of directories to add to the Python path.

        e.g.
        ``'/home/djangoprojects/myproject,/home/python/mylibrary'``.
        """


class Paste(Setting):
    name = "paste"
    section = "Server Mechanics"
    cli = ["--paste", "--paster"]
    meta = "STRING"
    validator = validate_string
    default = None
    desc = """\
        Load a PasteDeploy config file. The argument may contain a ``#``
        symbol followed by the name of an app section from the config file,
        e.g. ``production.ini#admin``.

        At this time, using alternate server blocks is not supported. Use the
        command line arguments to control server configuration instead.
        """


class OnStarting(Setting):
    name = "on_starting"
    section = "Server Hooks"
    validator = validate_callable(1)
    type = callable

    def on_starting(server):
        pass
    default = staticmethod(on_starting)
    desc = """\
        Called just before the master process is initialized.

        The callable needs to accept a single instance variable for the Arbiter.
        """


class OnReload(Setting):
    name = "on_reload"
    section = "Server Hooks"
    validator = validate_callable(1)
    type = callable

    def on_reload(server):
        pass
    default = staticmethod(on_reload)
    desc = """\
        Called to recycle workers during a reload via SIGHUP.

        The callable needs to accept a single instance variable for the Arbiter.
        """


class WhenReady(Setting):
    name = "when_ready"
    section = "Server Hooks"
    validator = validate_callable(1)
    type = callable

    def when_ready(server):
        pass
    default = staticmethod(when_ready)
    desc = """\
        Called just after the server is started.

        The callable needs to accept a single instance variable for the Arbiter.
        """


class Prefork(Setting):
    name = "pre_fork"
    section = "Server Hooks"
    validator = validate_callable(2)
    type = callable

    def pre_fork(server, worker):
        pass
    default = staticmethod(pre_fork)
    desc = """\
        Called just before a worker is forked.

        The callable needs to accept two instance variables for the Arbiter and
        new Worker.
        """


class Postfork(Setting):
    name = "post_fork"
    section = "Server Hooks"
    validator = validate_callable(2)
    type = callable

    def post_fork(server, worker):
        pass
    default = staticmethod(post_fork)
    desc = """\
        Called just after a worker has been forked.

        The callable needs to accept two instance variables for the Arbiter and
        new Worker.
        """


class PostWorkerInit(Setting):
    name = "post_worker_init"
    section = "Server Hooks"
    validator = validate_callable(1)
    type = callable

    def post_worker_init(worker):
        pass

    default = staticmethod(post_worker_init)
    desc = """\
        Called just after a worker has initialized the application.

        The callable needs to accept one instance variable for the initialized
        Worker.
        """


class WorkerInt(Setting):
    name = "worker_int"
    section = "Server Hooks"
    validator = validate_callable(1)
    type = callable

    def worker_int(worker):
        pass

    default = staticmethod(worker_int)
    desc = """\
        Called just after a worker exited on SIGINT or SIGQUIT.

        The callable needs to accept one instance variable for the initialized
        Worker.
        """


class WorkerAbort(Setting):
    name = "worker_abort"
    section = "Server Hooks"
    validator = validate_callable(1)
    type = callable

    def worker_abort(worker):
        pass

    default = staticmethod(worker_abort)
    desc = """\
        Called when a worker received the SIGABRT signal.

        This call generally happens on timeout.

        The callable needs to accept one instance variable for the initialized
        Worker.
        """


class PreExec(Setting):
    name = "pre_exec"
    section = "Server Hooks"
    validator = validate_callable(1)
    type = callable

    def pre_exec(server):
        pass
    default = staticmethod(pre_exec)
    desc = """\
        Called just before a new master process is forked.

        The callable needs to accept a single instance variable for the Arbiter.
        """


class PreRequest(Setting):
    name = "pre_request"
    section = "Server Hooks"
    validator = validate_callable(2)
    type = callable

    def pre_request(worker, req):
        worker.log.debug("%s %s", req.method, req.path)
    default = staticmethod(pre_request)
    desc = """\
        Called just before a worker processes the request.

        The callable needs to accept two instance variables for the Worker and
        the Request.
        """


class PostRequest(Setting):
    name = "post_request"
    section = "Server Hooks"
    validator = validate_post_request
    type = callable

    def post_request(worker, req, environ, resp):
        pass
    default = staticmethod(post_request)
    desc = """\
        Called after a worker processes the request.

        The callable needs to accept two instance variables for the Worker and
        the Request.
        """


class ChildExit(Setting):
    name = "child_exit"
    section = "Server Hooks"
    validator = validate_callable(2)
    type = callable

    def child_exit(server, worker):
        pass
    default = staticmethod(child_exit)
    desc = """\
        Called just after a worker has been exited, in the master process.

        The callable needs to accept two instance variables for the Arbiter and
        the just-exited Worker.

        .. versionadded:: 19.7
        """


class WorkerExit(Setting):
    name = "worker_exit"
    section = "Server Hooks"
    validator = validate_callable(2)
    type = callable

    def worker_exit(server, worker):
        pass
    default = staticmethod(worker_exit)
    desc = """\
        Called just after a worker has been exited, in the worker process.

        The callable needs to accept two instance variables for the Arbiter and
        the just-exited Worker.
        """


class NumWorkersChanged(Setting):
    name = "nworkers_changed"
    section = "Server Hooks"
    validator = validate_callable(3)
    type = callable

    def nworkers_changed(server, new_value, old_value):
        pass
    default = staticmethod(nworkers_changed)
    desc = """\
        Called just after *num_workers* has been changed.

        The callable needs to accept an instance variable of the Arbiter and
        two integers of number of workers after and before change.

        If the number of workers is set for the first time, *old_value* would
        be ``None``.
        """


class OnExit(Setting):
    name = "on_exit"
    section = "Server Hooks"
    validator = validate_callable(1)

    def on_exit(server):
        pass

    default = staticmethod(on_exit)
    desc = """\
        Called just before exiting Gunicorn.

        The callable needs to accept a single instance variable for the Arbiter.
        """


class NewSSLContext(Setting):
    name = "ssl_context"
    section = "Server Hooks"
    validator = validate_callable(2)
    type = callable

    def ssl_context(config, default_ssl_context_factory):
        return default_ssl_context_factory()

    default = staticmethod(ssl_context)
    desc = """\
        Called when SSLContext is needed.

        Allows customizing SSL context.

        The callable needs to accept an instance variable for the Config and
        a factory function that returns default SSLContext which is initialized
        with certificates, private key, cert_reqs, and ciphers according to
        config and can be further customized by the callable.
        The callable needs to return SSLContext object.

        Following example shows a configuration file that sets the minimum TLS version to 1.3:

        .. code-block:: python

            def ssl_context(conf, default_ssl_context_factory):
                import ssl
                context = default_ssl_context_factory()
                context.minimum_version = ssl.TLSVersion.TLSv1_3
                return context

        .. versionadded:: 21.0
        """


class ProxyProtocol(Setting):
    name = "proxy_protocol"
    section = "Server Mechanics"
    cli = ["--proxy-protocol"]
    validator = validate_bool
    default = False
    action = "store_true"
    desc = """\
        Enable detect PROXY protocol (PROXY mode).

        Allow using HTTP and Proxy together. It may be useful for work with
        stunnel as HTTPS frontend and Gunicorn as HTTP server.

        PROXY protocol: http://haproxy.1wt.eu/download/1.5/doc/proxy-protocol.txt

        Example for stunnel config::

            [https]
            protocol = proxy
            accept  = 443
            connect = 80
            cert = /etc/ssl/certs/stunnel.pem
            key = /etc/ssl/certs/stunnel.key
        """


class ProxyAllowFrom(Setting):
    name = "proxy_allow_ips"
    section = "Server Mechanics"
    cli = ["--proxy-allow-from"]
    validator = validate_string_to_addr_list
    default = "127.0.0.1,::1"
    desc = """\
        Front-end's IPs from which allowed accept proxy requests (comma separated).

        Set to ``*`` to disable checking of front-end IPs. This is useful for setups
        where you don't know in advance the IP address of front-end, but
        instead have ensured via other means that only your
        authorized front-ends can access Gunicorn.

        .. note::

            This option does not affect UNIX socket connections. Connections not associated with
            an IP address are treated as allowed, unconditionally.
        """


class KeyFile(Setting):
    name = "keyfile"
    section = "SSL"
    cli = ["--keyfile"]
    meta = "FILE"
    validator = validate_string
    default = None
    desc = """\
    SSL key file
    """


class CertFile(Setting):
    name = "certfile"
    section = "SSL"
    cli = ["--certfile"]
    meta = "FILE"
    validator = validate_string
    default = None
    desc = """\
    SSL certificate file
    """


class SSLVersion(Setting):
    name = "ssl_version"
    section = "SSL"
    cli = ["--ssl-version"]
    validator = validate_ssl_version

    if hasattr(ssl, "PROTOCOL_TLS"):
        default = ssl.PROTOCOL_TLS
    else:
        default = ssl.PROTOCOL_SSLv23

    default = ssl.PROTOCOL_SSLv23
    desc = """\
    SSL version to use (see stdlib ssl module's).

    .. deprecated:: 21.0
       The option is deprecated and it is currently ignored. Use :ref:`ssl-context` instead.

    ============= ============
    --ssl-version Description
    ============= ============
    SSLv3         SSLv3 is not-secure and is strongly discouraged.
    SSLv23        Alias for TLS. Deprecated in Python 3.6, use TLS.
    TLS           Negotiate highest possible version between client/server.
                  Can yield SSL. (Python 3.6+)
    TLSv1         TLS 1.0
    TLSv1_1       TLS 1.1 (Python 3.4+)
    TLSv1_2       TLS 1.2 (Python 3.4+)
    TLS_SERVER    Auto-negotiate the highest protocol version like TLS,
                  but only support server-side SSLSocket connections.
                  (Python 3.6+)
    ============= ============

    .. versionchanged:: 19.7
       The default value has been changed from ``ssl.PROTOCOL_TLSv1`` to
       ``ssl.PROTOCOL_SSLv23``.
    .. versionchanged:: 20.0
       This setting now accepts string names based on ``ssl.PROTOCOL_``
       constants.
    .. versionchanged:: 20.0.1
       The default value has been changed from ``ssl.PROTOCOL_SSLv23`` to
       ``ssl.PROTOCOL_TLS`` when Python >= 3.6 .
    """


class CertReqs(Setting):
    name = "cert_reqs"
    section = "SSL"
    cli = ["--cert-reqs"]
    validator = validate_pos_int
    default = ssl.CERT_NONE
    desc = """\
    Whether client certificate is required (see stdlib ssl module's)

    ===========  ===========================
    --cert-reqs      Description
    ===========  ===========================
    `0`          no client verification
    `1`          ssl.CERT_OPTIONAL
    `2`          ssl.CERT_REQUIRED
    ===========  ===========================
    """


class CACerts(Setting):
    name = "ca_certs"
    section = "SSL"
    cli = ["--ca-certs"]
    meta = "FILE"
    validator = validate_string
    default = None
    desc = """\
    CA certificates file
    """


class SuppressRaggedEOFs(Setting):
    name = "suppress_ragged_eofs"
    section = "SSL"
    cli = ["--suppress-ragged-eofs"]
    action = "store_true"
    default = True
    validator = validate_bool
    desc = """\
    Suppress ragged EOFs (see stdlib ssl module's)
    """


class DoHandshakeOnConnect(Setting):
    name = "do_handshake_on_connect"
    section = "SSL"
    cli = ["--do-handshake-on-connect"]
    validator = validate_bool
    action = "store_true"
    default = False
    desc = """\
    Whether to perform SSL handshake on socket connect (see stdlib ssl module's)
    """


class Ciphers(Setting):
    name = "ciphers"
    section = "SSL"
    cli = ["--ciphers"]
    validator = validate_string
    default = None
    desc = """\
    SSL Cipher suite to use, in the format of an OpenSSL cipher list.

    By default we use the default cipher list from Python's ``ssl`` module,
    which contains ciphers considered strong at the time of each Python
    release.

    As a recommended alternative, the Open Web App Security Project (OWASP)
    offers `a vetted set of strong cipher strings rated A+ to C-
    <https://www.owasp.org/index.php/TLS_Cipher_String_Cheat_Sheet>`_.
    OWASP provides details on user-agent compatibility at each security level.

    See the `OpenSSL Cipher List Format Documentation
    <https://www.openssl.org/docs/manmaster/man1/ciphers.html#CIPHER-LIST-FORMAT>`_
    for details on the format of an OpenSSL cipher list.
    """


class PasteGlobalConf(Setting):
    name = "raw_paste_global_conf"
    action = "append"
    section = "Server Mechanics"
    cli = ["--paste-global"]
    meta = "CONF"
    validator = validate_list_string
    default = []

    desc = """\
        Set a PasteDeploy global config variable in ``key=value`` form.

        The option can be specified multiple times.

        The variables are passed to the PasteDeploy entrypoint. Example::

            $ gunicorn -b 127.0.0.1:8000 --paste development.ini --paste-global FOO=1 --paste-global BAR=2

        .. versionadded:: 19.7
        """


class PermitObsoleteFolding(Setting):
    name = "permit_obsolete_folding"
    section = "Server Mechanics"
    cli = ["--permit-obsolete-folding"]
    validator = validate_bool
    action = "store_true"
    default = False
    desc = """\
        Permit requests employing obsolete HTTP line folding mechanism

        The folding mechanism was deprecated by rfc7230 Section 3.2.4 and will not be
         employed in HTTP request headers from standards-compliant HTTP clients.

        This option is provided to diagnose backwards-incompatible changes.
        Use with care and only if necessary. Temporary; the precise effect of this option may
        change in a future version, or it may be removed altogether.

        .. versionadded:: 23.0.0
        """


class StripHeaderSpaces(Setting):
    name = "strip_header_spaces"
    section = "Server Mechanics"
    cli = ["--strip-header-spaces"]
    validator = validate_bool
    action = "store_true"
    default = False
    desc = """\
        Strip spaces present between the header name and the the ``:``.

        This is known to induce vulnerabilities and is not compliant with the HTTP/1.1 standard.
        See https://portswigger.net/research/http-desync-attacks-request-smuggling-reborn.

        Use with care and only if necessary. Deprecated; scheduled for removal in 25.0.0

        .. versionadded:: 20.0.1
        """


class PermitUnconventionalHTTPMethod(Setting):
    name = "permit_unconventional_http_method"
    section = "Server Mechanics"
    cli = ["--permit-unconventional-http-method"]
    validator = validate_bool
    action = "store_true"
    default = False
    desc = """\
        Permit HTTP methods not matching conventions, such as IANA registration guidelines

        This permits request methods of length less than 3 or more than 20,
        methods with lowercase characters or methods containing the # character.
        HTTP methods are case sensitive by definition, and merely uppercase by convention.

        If unset, Gunicorn will apply nonstandard restrictions and cause 400 response status
        in cases where otherwise 501 status is expected. While this option does modify that
        behaviour, it should not be depended upon to guarantee standards-compliant behaviour.
        Rather, it is provided temporarily, to assist in diagnosing backwards-incompatible
        changes around the incomplete application of those restrictions.

        Use with care and only if necessary. Temporary; scheduled for removal in 24.0.0

        .. versionadded:: 22.0.0
        """


class PermitUnconventionalHTTPVersion(Setting):
    name = "permit_unconventional_http_version"
    section = "Server Mechanics"
    cli = ["--permit-unconventional-http-version"]
    validator = validate_bool
    action = "store_true"
    default = False
    desc = """\
        Permit HTTP version not matching conventions of 2023

        This disables the refusal of likely malformed request lines.
        It is unusual to specify HTTP 1 versions other than 1.0 and 1.1.

        This option is provided to diagnose backwards-incompatible changes.
        Use with care and only if necessary. Temporary; the precise effect of this option may
        change in a future version, or it may be removed altogether.

        .. versionadded:: 22.0.0
        """


class CasefoldHTTPMethod(Setting):
    name = "casefold_http_method"
    section = "Server Mechanics"
    cli = ["--casefold-http-method"]
    validator = validate_bool
    action = "store_true"
    default = False
    desc = """\
         Transform received HTTP methods to uppercase

         HTTP methods are case sensitive by definition, and merely uppercase by convention.

         This option is provided because previous versions of gunicorn defaulted to this behaviour.

         Use with care and only if necessary. Deprecated; scheduled for removal in 24.0.0

         .. versionadded:: 22.0.0
         """


def validate_header_map_behaviour(val):
    # FIXME: refactor all of this subclassing stdlib argparse

    if val is None:
        return

    if not isinstance(val, str):
        raise TypeError("Invalid type for casting: %s" % val)
    if val.lower().strip() == "drop":
        return "drop"
    elif val.lower().strip() == "refuse":
        return "refuse"
    elif val.lower().strip() == "dangerous":
        return "dangerous"
    else:
        raise ValueError("Invalid header map behaviour: %s" % val)


class ForwarderHeaders(Setting):
    name = "forwarder_headers"
    section = "Server Mechanics"
    cli = ["--forwarder-headers"]
    validator = validate_string_to_list
    default = "SCRIPT_NAME,PATH_INFO"
    desc = """\

        A list containing upper-case header field names that the front-end proxy
        (see :ref:`forwarded-allow-ips`) sets, to be used in WSGI environment.

        This option has no effect for headers not present in the request.

        This option can be used to transfer ``SCRIPT_NAME``, ``PATH_INFO``
        and ``REMOTE_USER``.

        It is important that your front-end proxy configuration ensures that
        the headers defined here can not be passed directly from the client.
        """


class HeaderMap(Setting):
    name = "header_map"
    section = "Server Mechanics"
    cli = ["--header-map"]
    validator = validate_header_map_behaviour
    default = "drop"
    desc = """\
        Configure how header field names are mapped into environ

        Headers containing underscores are permitted by RFC9110,
        but gunicorn joining headers of different names into
        the same environment variable will dangerously confuse applications as to which is which.

        The safe default ``drop`` is to silently drop headers that cannot be unambiguously mapped.
        The value ``refuse`` will return an error if a request contains *any* such header.
        The value ``dangerous`` matches the previous, not advisable, behaviour of mapping different
        header field names into the same environ name.

        If the source is permitted as explained in :ref:`forwarded-allow-ips`, *and* the header name is
        present in :ref:`forwarder-headers`, the header is mapped into environment regardless of
        the state of this setting.

        Use with care and only if necessary and after considering if your problem could
        instead be solved by specifically renaming or rewriting only the intended headers
        on a proxy in front of Gunicorn.

        .. versionadded:: 22.0.0
        """
