#
# This file is part of gunicorn released under the MIT license.
# See the NOTICE for more information.
import ast
import email.utils
import errno
import fcntl
import html
import importlib
import inspect
import io
import logging
import os
import pwd
import random
import re
import socket
import sys
import textwrap
import time
import traceback
import warnings

try:
    import importlib.metadata as importlib_metadata
except (ModuleNotFoundError, ImportError):
    import importlib_metadata

from gunicorn.errors import AppImportError
from gunicorn.workers import SUPPORTED_WORKERS
import urllib.parse

REDIRECT_TO = getattr(os, 'devnull', '/dev/null')

# Server and Date aren't technically hop-by-hop
# headers, but they are in the purview of the
# origin server which the WSGI spec says we should
# act like. So we drop them and add our own.
#
# In the future, concatenation server header values
# might be better, but nothing else does it and
# dropping them is easier.
hop_headers = set("""
    connection keep-alive proxy-authenticate proxy-authorization
    te trailers transfer-encoding upgrade
    server date
    """.split())

try:
    from setproctitle import setproctitle

    def _setproctitle(title):
        setproctitle("gunicorn: %s" % title)
except ImportError:
    def _setproctitle(title):
        pass


def load_entry_point(distribution, group, name):
    dist_obj = importlib_metadata.distribution(distribution)
    eps = [ep for ep in dist_obj.entry_points
           if ep.group == group and ep.name == name]
    if not eps:
        raise ImportError("Entry point %r not found" % ((group, name),))
    return eps[0].load()


def load_class(uri, default="gunicorn.workers.sync.SyncWorker",
               section="gunicorn.workers"):
    if inspect.isclass(uri):
        return uri
    if uri.startswith("egg:"):
        # uses entry points
        entry_str = uri.split("egg:")[1]
        try:
            dist, name = entry_str.rsplit("#", 1)
        except ValueError:
            dist = entry_str
            name = default

        try:
            return load_entry_point(dist, section, name)
        except Exception:
            exc = traceback.format_exc()
            msg = "class uri %r invalid or not found: \n\n[%s]"
            raise RuntimeError(msg % (uri, exc))
    else:
        components = uri.split('.')
        if len(components) == 1:
            while True:
                if uri.startswith("#"):
                    uri = uri[1:]

                if uri in SUPPORTED_WORKERS:
                    components = SUPPORTED_WORKERS[uri].split(".")
                    break

                try:
                    return load_entry_point(
                        "gunicorn", section, uri
                    )
                except Exception:
                    exc = traceback.format_exc()
                    msg = "class uri %r invalid or not found: \n\n[%s]"
                    raise RuntimeError(msg % (uri, exc))

        klass = components.pop(-1)

        try:
            mod = importlib.import_module('.'.join(components))
        except Exception:
            exc = traceback.format_exc()
            msg = "class uri %r invalid or not found: \n\n[%s]"
            raise RuntimeError(msg % (uri, exc))
        return getattr(mod, klass)


positionals = (
    inspect.Parameter.POSITIONAL_ONLY,
    inspect.Parameter.POSITIONAL_OR_KEYWORD,
)


def get_arity(f):
    sig = inspect.signature(f)
    arity = 0

    for param in sig.parameters.values():
        if param.kind in positionals:
            arity += 1

    return arity


def get_username(uid):
    """ get the username for a user id"""
    return pwd.getpwuid(uid).pw_name


def set_owner_process(uid, gid, initgroups=False):
    """ set user and group of workers processes """

    if gid:
        if uid:
            try:
                username = get_username(uid)
            except KeyError:
                initgroups = False

        # versions of python < 2.6.2 don't manage unsigned int for
        # groups like on osx or fedora
        gid = abs(gid) & 0x7FFFFFFF

        if initgroups:
            os.initgroups(username, gid)
        elif gid != os.getgid():
            os.setgid(gid)

    if uid and uid != os.getuid():
        os.setuid(uid)


def chown(path, uid, gid):
    os.chown(path, uid, gid)


if sys.platform.startswith("win"):
    def _waitfor(func, pathname, waitall=False):
        # Perform the operation
        func(pathname)
        # Now setup the wait loop
        if waitall:
            dirname = pathname
        else:
            dirname, name = os.path.split(pathname)
            dirname = dirname or '.'
        # Check for `pathname` to be removed from the filesystem.
        # The exponential backoff of the timeout amounts to a total
        # of ~1 second after which the deletion is probably an error
        # anyway.
        # Testing on a i7@4.3GHz shows that usually only 1 iteration is
        # required when contention occurs.
        timeout = 0.001
        while timeout < 1.0:
            # Note we are only testing for the existence of the file(s) in
            # the contents of the directory regardless of any security or
            # access rights.  If we have made it this far, we have sufficient
            # permissions to do that much using Python's equivalent of the
            # Windows API FindFirstFile.
            # Other Windows APIs can fail or give incorrect results when
            # dealing with files that are pending deletion.
            L = os.listdir(dirname)
            if not L if waitall else name in L:
                return
            # Increase the timeout and try again
            time.sleep(timeout)
            timeout *= 2
        warnings.warn('tests may fail, delete still pending for ' + pathname,
                      RuntimeWarning, stacklevel=4)

    def _unlink(filename):
        _waitfor(os.unlink, filename)
else:
    _unlink = os.unlink


def unlink(filename):
    try:
        _unlink(filename)
    except OSError as error:
        # The filename need not exist.
        if error.errno not in (errno.ENOENT, errno.ENOTDIR):
            raise


def is_ipv6(addr):
    try:
        socket.inet_pton(socket.AF_INET6, addr)
    except OSError:  # not a valid address
        return False
    except ValueError:  # ipv6 not supported on this platform
        return False
    return True


def parse_address(netloc, default_port='8000'):
    if re.match(r'unix:(//)?', netloc):
        return re.split(r'unix:(//)?', netloc)[-1]

    if netloc.startswith("fd://"):
        fd = netloc[5:]
        try:
            return int(fd)
        except ValueError:
            raise RuntimeError("%r is not a valid file descriptor." % fd) from None

    if netloc.startswith("tcp://"):
        netloc = netloc.split("tcp://")[1]
    host, port = netloc, default_port

    if '[' in netloc and ']' in netloc:
        host = netloc.split(']')[0][1:]
        port = (netloc.split(']:') + [default_port])[1]
    elif ':' in netloc:
        host, port = (netloc.split(':') + [default_port])[:2]
    elif netloc == "":
        host, port = "0.0.0.0", default_port

    try:
        port = int(port)
    except ValueError:
        raise RuntimeError("%r is not a valid port number." % port)

    return host.lower(), port


def close_on_exec(fd):
    flags = fcntl.fcntl(fd, fcntl.F_GETFD)
    flags |= fcntl.FD_CLOEXEC
    fcntl.fcntl(fd, fcntl.F_SETFD, flags)


def set_non_blocking(fd):
    flags = fcntl.fcntl(fd, fcntl.F_GETFL) | os.O_NONBLOCK
    fcntl.fcntl(fd, fcntl.F_SETFL, flags)


def close(sock):
    try:
        sock.close()
    except OSError:
        pass


try:
    from os import closerange
except ImportError:
    def closerange(fd_low, fd_high):
        # Iterate through and close all file descriptors.
        for fd in range(fd_low, fd_high):
            try:
                os.close(fd)
            except OSError:  # ERROR, fd wasn't open to begin with (ignored)
                pass


def write_chunk(sock, data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    chunk_size = "%X\r\n" % len(data)
    chunk = b"".join([chunk_size.encode('utf-8'), data, b"\r\n"])
    sock.sendall(chunk)


def write(sock, data, chunked=False):
    if chunked:
        return write_chunk(sock, data)
    sock.sendall(data)


def write_nonblock(sock, data, chunked=False):
    timeout = sock.gettimeout()
    if timeout != 0.0:
        try:
            sock.setblocking(0)
            return write(sock, data, chunked)
        finally:
            sock.setblocking(1)
    else:
        return write(sock, data, chunked)


def write_error(sock, status_int, reason, mesg):
    html_error = textwrap.dedent("""\
    <html>
      <head>
        <title>%(reason)s</title>
      </head>
      <body>
        <h1><p>%(reason)s</p></h1>
        %(mesg)s
      </body>
    </html>
    """) % {"reason": reason, "mesg": html.escape(mesg)}

    http = textwrap.dedent("""\
    HTTP/1.1 %s %s\r
    Connection: close\r
    Content-Type: text/html\r
    Content-Length: %d\r
    \r
    %s""") % (str(status_int), reason, len(html_error), html_error)
    write_nonblock(sock, http.encode('latin1'))


def _called_with_wrong_args(f):
    """Check whether calling a function raised a ``TypeError`` because
    the call failed or because something in the function raised the
    error.

    :param f: The function that was called.
    :return: ``True`` if the call failed.
    """
    tb = sys.exc_info()[2]

    try:
        while tb is not None:
            if tb.tb_frame.f_code is f.__code__:
                # In the function, it was called successfully.
                return False

            tb = tb.tb_next

        # Didn't reach the function.
        return True
    finally:
        # Delete tb to break a circular reference in Python 2.
        # https://docs.python.org/2/library/sys.html#sys.exc_info
        del tb


def import_app(module):
    parts = module.split(":", 1)
    if len(parts) == 1:
        obj = "application"
    else:
        module, obj = parts[0], parts[1]

    try:
        mod = importlib.import_module(module)
    except ImportError:
        if module.endswith(".py") and os.path.exists(module):
            msg = "Failed to find application, did you mean '%s:%s'?"
            raise ImportError(msg % (module.rsplit(".", 1)[0], obj))
        raise

    # Parse obj as a single expression to determine if it's a valid
    # attribute name or function call.
    try:
        expression = ast.parse(obj, mode="eval").body
    except SyntaxError:
        raise AppImportError(
            "Failed to parse %r as an attribute name or function call." % obj
        )

    if isinstance(expression, ast.Name):
        name = expression.id
        args = kwargs = None
    elif isinstance(expression, ast.Call):
        # Ensure the function name is an attribute name only.
        if not isinstance(expression.func, ast.Name):
            raise AppImportError("Function reference must be a simple name: %r" % obj)

        name = expression.func.id

        # Parse the positional and keyword arguments as literals.
        try:
            args = [ast.literal_eval(arg) for arg in expression.args]
            kwargs = {kw.arg: ast.literal_eval(kw.value) for kw in expression.keywords}
        except ValueError:
            # literal_eval gives cryptic error messages, show a generic
            # message with the full expression instead.
            raise AppImportError(
                "Failed to parse arguments as literal values: %r" % obj
            )
    else:
        raise AppImportError(
            "Failed to parse %r as an attribute name or function call." % obj
        )

    is_debug = logging.root.level == logging.DEBUG
    try:
        app = getattr(mod, name)
    except AttributeError:
        if is_debug:
            traceback.print_exception(*sys.exc_info())
        raise AppImportError("Failed to find attribute %r in %r." % (name, module))

    # If the expression was a function call, call the retrieved object
    # to get the real application.
    if args is not None:
        try:
            app = app(*args, **kwargs)
        except TypeError as e:
            # If the TypeError was due to bad arguments to the factory
            # function, show Python's nice error message without a
            # traceback.
            if _called_with_wrong_args(app):
                raise AppImportError(
                    "".join(traceback.format_exception_only(TypeError, e)).strip()
                )

            # Otherwise it was raised from within the function, show the
            # full traceback.
            raise

    if app is None:
        raise AppImportError("Failed to find application object: %r" % obj)

    if not callable(app):
        raise AppImportError("Application object must be callable.")
    return app


def getcwd():
    # get current path, try to use PWD env first
    try:
        a = os.stat(os.environ['PWD'])
        b = os.stat(os.getcwd())
        if a.st_ino == b.st_ino and a.st_dev == b.st_dev:
            cwd = os.environ['PWD']
        else:
            cwd = os.getcwd()
    except Exception:
        cwd = os.getcwd()
    return cwd


def http_date(timestamp=None):
    """Return the current date and time formatted for a message header."""
    if timestamp is None:
        timestamp = time.time()
    s = email.utils.formatdate(timestamp, localtime=False, usegmt=True)
    return s


def is_hoppish(header):
    return header.lower().strip() in hop_headers


def daemonize(enable_stdio_inheritance=False):
    """\
    Standard daemonization of a process.
    http://www.faqs.org/faqs/unix-faq/programmer/faq/ section 1.7
    """
    if 'GUNICORN_FD' not in os.environ:
        if os.fork():
            os._exit(0)
        os.setsid()

        if os.fork():
            os._exit(0)

        os.umask(0o22)

        # In both the following any file descriptors above stdin
        # stdout and stderr are left untouched. The inheritance
        # option simply allows one to have output go to a file
        # specified by way of shell redirection when not wanting
        # to use --error-log option.

        if not enable_stdio_inheritance:
            # Remap all of stdin, stdout and stderr on to
            # /dev/null. The expectation is that users have
            # specified the --error-log option.

            closerange(0, 3)

            fd_null = os.open(REDIRECT_TO, os.O_RDWR)
            # PEP 446, make fd for /dev/null inheritable
            os.set_inheritable(fd_null, True)

            # expect fd_null to be always 0 here, but in-case not ...
            if fd_null != 0:
                os.dup2(fd_null, 0)

            os.dup2(fd_null, 1)
            os.dup2(fd_null, 2)

        else:
            fd_null = os.open(REDIRECT_TO, os.O_RDWR)

            # Always redirect stdin to /dev/null as we would
            # never expect to need to read interactive input.

            if fd_null != 0:
                os.close(0)
                os.dup2(fd_null, 0)

            # If stdout and stderr are still connected to
            # their original file descriptors we check to see
            # if they are associated with terminal devices.
            # When they are we map them to /dev/null so that
            # are still detached from any controlling terminal
            # properly. If not we preserve them as they are.
            #
            # If stdin and stdout were not hooked up to the
            # original file descriptors, then all bets are
            # off and all we can really do is leave them as
            # they were.
            #
            # This will allow 'gunicorn ... > output.log 2>&1'
            # to work with stdout/stderr going to the file
            # as expected.
            #
            # Note that if using --error-log option, the log
            # file specified through shell redirection will
            # only be used up until the log file specified
            # by the option takes over. As it replaces stdout
            # and stderr at the file descriptor level, then
            # anything using stdout or stderr, including having
            # cached a reference to them, will still work.

            def redirect(stream, fd_expect):
                try:
                    fd = stream.fileno()
                    if fd == fd_expect and stream.isatty():
                        os.close(fd)
                        os.dup2(fd_null, fd)
                except AttributeError:
                    pass

            redirect(sys.stdout, 1)
            redirect(sys.stderr, 2)


def seed():
    try:
        random.seed(os.urandom(64))
    except NotImplementedError:
        random.seed('%s.%s' % (time.time(), os.getpid()))


def check_is_writable(path):
    try:
        with open(path, 'a') as f:
            f.close()
    except OSError as e:
        raise RuntimeError("Error: '%s' isn't writable [%r]" % (path, e))


def to_bytestring(value, encoding="utf8"):
    """Converts a string argument to a byte string"""
    if isinstance(value, bytes):
        return value
    if not isinstance(value, str):
        raise TypeError('%r is not a string' % value)

    return value.encode(encoding)


def has_fileno(obj):
    if not hasattr(obj, "fileno"):
        return False

    # check BytesIO case and maybe others
    try:
        obj.fileno()
    except (AttributeError, OSError, io.UnsupportedOperation):
        return False

    return True


def warn(msg):
    print("!!!", file=sys.stderr)

    lines = msg.splitlines()
    for i, line in enumerate(lines):
        if i == 0:
            line = "WARNING: %s" % line
        print("!!! %s" % line, file=sys.stderr)

    print("!!!\n", file=sys.stderr)
    sys.stderr.flush()


def make_fail_app(msg):
    msg = to_bytestring(msg)

    def app(environ, start_response):
        start_response("500 Internal Server Error", [
            ("Content-Type", "text/plain"),
            ("Content-Length", str(len(msg)))
        ])
        return [msg]

    return app


def split_request_uri(uri):
    if uri.startswith("//"):
        # When the path starts with //, urlsplit considers it as a
        # relative uri while the RFC says we should consider it as abs_path
        # http://www.w3.org/Protocols/rfc2616/rfc2616-sec5.html#sec5.1.2
        # We use temporary dot prefix to workaround this behaviour
        parts = urllib.parse.urlsplit("." + uri)
        return parts._replace(path=parts.path[1:])

    return urllib.parse.urlsplit(uri)


# From six.reraise
def reraise(tp, value, tb=None):
    try:
        if value is None:
            value = tp()
        if value.__traceback__ is not tb:
            raise value.with_traceback(tb)
        raise value
    finally:
        value = None
        tb = None


def bytes_to_str(b):
    if isinstance(b, str):
        return b
    return str(b, 'latin1')


def unquote_to_wsgi_str(string):
    return urllib.parse.unquote_to_bytes(string).decode('latin-1')
