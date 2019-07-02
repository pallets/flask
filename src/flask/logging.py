# -*- coding: utf-8 -*-
"""
flask.logging
~~~~~~~~~~~~~

:copyright: 2010 Pallets
:license: BSD-3-Clause
"""
from __future__ import absolute_import

import logging
import sys
import warnings

from werkzeug.local import LocalProxy

from .globals import request


@LocalProxy
def wsgi_errors_stream():
    """Find the most appropriate error stream for the application. If a request
    is active, log to ``wsgi.errors``, otherwise use ``sys.stderr``.

    If you configure your own :class:`logging.StreamHandler`, you may want to
    use this for the stream. If you are using file or dict configuration and
    can't import this directly, you can refer to it as
    ``ext://flask.logging.wsgi_errors_stream``.
    """
    return request.environ["wsgi.errors"] if request else sys.stderr


def has_level_handler(logger):
    """Check if there is a handler in the logging chain that will handle the
    given logger's :meth:`effective level <~logging.Logger.getEffectiveLevel>`.
    """
    level = logger.getEffectiveLevel()
    current = logger

    while current:
        if any(handler.level <= level for handler in current.handlers):
            return True

        if not current.propagate:
            break

        current = current.parent

    return False


#: Log messages to :func:`~flask.logging.wsgi_errors_stream` with the format
#: ``[%(asctime)s] %(levelname)s in %(module)s: %(message)s``.
default_handler = logging.StreamHandler(wsgi_errors_stream)
default_handler.setFormatter(
    logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
)


def _has_config(logger):
    """Decide if a logger has direct configuration applied by checking
    its properties against the defaults.

    :param logger: The :class:`~logging.Logger` to inspect.
    """
    return (
        logger.level != logging.NOTSET
        or logger.handlers
        or logger.filters
        or not logger.propagate
    )


def create_logger(app):
    """Get the the Flask apps's logger and configure it if needed.

    The logger name will be the same as
    :attr:`app.import_name <flask.Flask.name>`.

    When :attr:`~flask.Flask.debug` is enabled, set the logger level to
    :data:`logging.DEBUG` if it is not set.

    If there is no handler for the logger's effective level, add a
    :class:`~logging.StreamHandler` for
    :func:`~flask.logging.wsgi_errors_stream` with a basic format.
    """
    logger = logging.getLogger(app.name)

    # 1.1.0 changes name of logger, warn if config is detected for old
    # name and not new name
    for old_name in ("flask.app", "flask"):
        old_logger = logging.getLogger(old_name)

        if _has_config(old_logger) and not _has_config(logger):
            warnings.warn(
                "'app.logger' is named '{name}' for this application,"
                " but configuration was found for '{old_name}', which"
                " no longer has an effect. The logging configuration"
                " should be moved to '{name}'.".format(name=app.name, old_name=old_name)
            )
            break

    if app.debug and not logger.level:
        logger.setLevel(logging.DEBUG)

    if not has_level_handler(logger):
        logger.addHandler(default_handler)

    return logger
