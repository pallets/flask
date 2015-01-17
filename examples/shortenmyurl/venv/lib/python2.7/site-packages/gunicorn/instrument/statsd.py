# -*- coding: utf-8 -
#
# This file is part of gunicorn released under the MIT license.
# See the NOTICE for more information.

"Bare-bones implementation of statsD's protocol, client-side"

import socket
import logging
from gunicorn.glogging import Logger

# Instrumentation constants
STATSD_DEFAULT_PORT = 8125
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
        """host, port: statsD server
        """
        Logger.__init__(self, cfg)
        try:
            host, port = cfg.statsd_host
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.connect((host, int(port)))
        except Exception:
            self.sock = None

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

    # Special treatement for info, the most common log level
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
            if msg is not None and len(msg) > 0:
                Logger.log(self, lvl, msg, *args, **kwargs)
        except Exception:
            pass


    # access logging
    def access(self, resp, req, environ, request_time):
        """Measure request duration
        request_time is a datetime.timedelta
        """
        Logger.access(self, resp, req, environ, request_time)
        duration_in_ms = request_time.seconds * 1000 + float(request_time.microseconds)/10**3
        self.histogram("gunicorn.request.duration", duration_in_ms)
        self.increment("gunicorn.requests", 1)
        self.increment("gunicorn.request.status.%d" % int(resp.status.split()[0]), 1)

    # statsD methods
    # you can use those directly if you want
    def gauge(self, name, value):
        try:
            if self.sock:
                self.sock.send("{0}:{1}|g".format(name, value))
        except Exception:
            pass

    def increment(self, name, value, sampling_rate=1.0):
        try:
            if self.sock:
                self.sock.send("{0}:{1}|c|@{2}".format(name, value, sampling_rate))
        except Exception:
            pass

    def decrement(self, name, value, sampling_rate=1.0):
        try:
            if self.sock:
                self.sock.send("{0}:-{1}|c|@{2}".format(name, value, sampling_rate))
        except Exception:
            pass

    def histogram(self, name, value):
        try:
            if self.sock:
                self.sock.send("{0}:{1}|ms".format(name, value))
        except Exception:
            pass
