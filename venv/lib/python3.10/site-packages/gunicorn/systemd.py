#
# This file is part of gunicorn released under the MIT license.
# See the NOTICE for more information.

import os
import socket

SD_LISTEN_FDS_START = 3


def listen_fds(unset_environment=True):
    """
    Get the number of sockets inherited from systemd socket activation.

    :param unset_environment: clear systemd environment variables unless False
    :type unset_environment: bool
    :return: the number of sockets to inherit from systemd socket activation
    :rtype: int

    Returns zero immediately if $LISTEN_PID is not set to the current pid.
    Otherwise, returns the number of systemd activation sockets specified by
    $LISTEN_FDS.

    When $LISTEN_PID matches the current pid, unsets the environment variables
    unless the ``unset_environment`` flag is ``False``.

    .. note::
        Unlike the sd_listen_fds C function, this implementation does not set
        the FD_CLOEXEC flag because the gunicorn arbiter never needs to do this.

    .. seealso::
        `<https://www.freedesktop.org/software/systemd/man/sd_listen_fds.html>`_

    """
    fds = int(os.environ.get('LISTEN_FDS', 0))
    listen_pid = int(os.environ.get('LISTEN_PID', 0))

    if listen_pid != os.getpid():
        return 0

    if unset_environment:
        os.environ.pop('LISTEN_PID', None)
        os.environ.pop('LISTEN_FDS', None)

    return fds


def sd_notify(state, logger, unset_environment=False):
    """Send a notification to systemd. state is a string; see
    the man page of sd_notify (http://www.freedesktop.org/software/systemd/man/sd_notify.html)
    for a description of the allowable values.

    If the unset_environment parameter is True, sd_notify() will unset
    the $NOTIFY_SOCKET environment variable before returning (regardless of
    whether the function call itself succeeded or not). Further calls to
    sd_notify() will then fail, but the variable is no longer inherited by
    child processes.
    """

    addr = os.environ.get('NOTIFY_SOCKET')
    if addr is None:
        # not run in a service, just a noop
        return
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM | socket.SOCK_CLOEXEC)
        if addr[0] == '@':
            addr = '\0' + addr[1:]
        sock.connect(addr)
        sock.sendall(state.encode('utf-8'))
    except Exception:
        logger.debug("Exception while invoking sd_notify()", exc_info=True)
    finally:
        if unset_environment:
            os.environ.pop('NOTIFY_SOCKET')
        sock.close()
