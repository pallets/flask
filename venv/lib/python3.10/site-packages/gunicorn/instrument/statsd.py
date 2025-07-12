#
# This file is part of gunicorn released under the MIT license.
# See the NOTICE for more information.

"Bare-bones implementation of statsD's protocol, client-side"

import logging
import socket
from re import sub

from gunicorn.glogging import Logger

# Instrumentation constants
METRIC_VAR = "metric"
VALUE_VAR = "value"
MTYPE_VAR = "mtype"
GAUGE_TYPE = "gauge"
COUNTER_TYPE = "counter"
HISTOGRAM_TYPE = "histogram"


class Statsd(Logger):
    """statsD-based instrumentation, that passes as a logger
    """
    def __init__(self, cfg):
        Logger.__init__(self, cfg)
        self.prefix = sub(r"^(.+[^.]+)\.*$", "\\g<1>.", cfg.statsd_prefix)

        if isinstance(cfg.statsd_host, str):
            address_family = socket.AF_UNIX
        else:
            address_family = socket.AF_INET

        try:
            self.sock = socket.socket(address_family, socket.SOCK_DGRAM)
            self.sock.connect(cfg.statsd_host)
        except Exception:
            self.sock = None

        self.dogstatsd_tags = cfg.dogstatsd_tags

    # Log errors and warnings
    def critical(self, msg, *args, **kwargs):
        Logger.critical(self, msg, *args, **kwargs)
        self.increment("gunicorn.log.critical", 1)

    def error(self, msg, *args, **kwargs):
        Logger.error(self, msg, *args, **kwargs)
        self.increment("gunicorn.log.error", 1)

    def warning(self, msg, *args, **kwargs):
        Logger.warning(self, msg, *args, **kwargs)
        self.increment("gunicorn.log.warning", 1)

    def exception(self, msg, *args, **kwargs):
        Logger.exception(self, msg, *args, **kwargs)
        self.increment("gunicorn.log.exception", 1)

    # Special treatment for info, the most common log level
    def info(self, msg, *args, **kwargs):
        self.log(logging.INFO, msg, *args, **kwargs)

    # skip the run-of-the-mill logs
    def debug(self, msg, *args, **kwargs):
        self.log(logging.DEBUG, msg, *args, **kwargs)

    def log(self, lvl, msg, *args, **kwargs):
        """Log a given statistic if metric, value and type are present
        """
        try:
            extra = kwargs.get("extra", None)
            if extra is not None:
                metric = extra.get(METRIC_VAR, None)
                value = extra.get(VALUE_VAR, None)
                typ = extra.get(MTYPE_VAR, None)
                if metric and value and typ:
                    if typ == GAUGE_TYPE:
                        self.gauge(metric, value)
                    elif typ == COUNTER_TYPE:
                        self.increment(metric, value)
                    elif typ == HISTOGRAM_TYPE:
                        self.histogram(metric, value)
                    else:
                        pass

            # Log to parent logger only if there is something to say
            if msg:
                Logger.log(self, lvl, msg, *args, **kwargs)
        except Exception:
            Logger.warning(self, "Failed to log to statsd", exc_info=True)

    # access logging
    def access(self, resp, req, environ, request_time):
        """Measure request duration
        request_time is a datetime.timedelta
        """
        Logger.access(self, resp, req, environ, request_time)
        duration_in_ms = request_time.seconds * 1000 + float(request_time.microseconds) / 10 ** 3
        status = resp.status
        if isinstance(status, bytes):
            status = status.decode('utf-8')
        if isinstance(status, str):
            status = int(status.split(None, 1)[0])
        self.histogram("gunicorn.request.duration", duration_in_ms)
        self.increment("gunicorn.requests", 1)
        self.increment("gunicorn.request.status.%d" % status, 1)

    # statsD methods
    # you can use those directly if you want
    def gauge(self, name, value):
        self._sock_send("{0}{1}:{2}|g".format(self.prefix, name, value))

    def increment(self, name, value, sampling_rate=1.0):
        self._sock_send("{0}{1}:{2}|c|@{3}".format(self.prefix, name, value, sampling_rate))

    def decrement(self, name, value, sampling_rate=1.0):
        self._sock_send("{0}{1}:-{2}|c|@{3}".format(self.prefix, name, value, sampling_rate))

    def histogram(self, name, value):
        self._sock_send("{0}{1}:{2}|ms".format(self.prefix, name, value))

    def _sock_send(self, msg):
        try:
            if isinstance(msg, str):
                msg = msg.encode("ascii")

            # http://docs.datadoghq.com/guides/dogstatsd/#datagram-format
            if self.dogstatsd_tags:
                msg = msg + b"|#" + self.dogstatsd_tags.encode('ascii')

            if self.sock:
                self.sock.send(msg)
        except Exception:
            Logger.warning(self, "Error sending message to statsd", exc_info=True)
