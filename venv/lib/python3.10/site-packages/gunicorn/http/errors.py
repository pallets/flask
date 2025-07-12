#
# This file is part of gunicorn released under the MIT license.
# See the NOTICE for more information.

# We don't need to call super() in __init__ methods of our
# BaseException and Exception classes because we also define
# our own __str__ methods so there is no need to pass 'message'
# to the base class to get a meaningful output from 'str(exc)'.
# pylint: disable=super-init-not-called


class ParseException(Exception):
    pass


class NoMoreData(IOError):
    def __init__(self, buf=None):
        self.buf = buf

    def __str__(self):
        return "No more data after: %r" % self.buf


class ConfigurationProblem(ParseException):
    def __init__(self, info):
        self.info = info
        self.code = 500

    def __str__(self):
        return "Configuration problem: %s" % self.info


class InvalidRequestLine(ParseException):
    def __init__(self, req):
        self.req = req
        self.code = 400

    def __str__(self):
        return "Invalid HTTP request line: %r" % self.req


class InvalidRequestMethod(ParseException):
    def __init__(self, method):
        self.method = method

    def __str__(self):
        return "Invalid HTTP method: %r" % self.method


class InvalidHTTPVersion(ParseException):
    def __init__(self, version):
        self.version = version

    def __str__(self):
        return "Invalid HTTP Version: %r" % (self.version,)


class InvalidHeader(ParseException):
    def __init__(self, hdr, req=None):
        self.hdr = hdr
        self.req = req

    def __str__(self):
        return "Invalid HTTP Header: %r" % self.hdr


class ObsoleteFolding(ParseException):
    def __init__(self, hdr):
        self.hdr = hdr

    def __str__(self):
        return "Obsolete line folding is unacceptable: %r" % (self.hdr, )


class InvalidHeaderName(ParseException):
    def __init__(self, hdr):
        self.hdr = hdr

    def __str__(self):
        return "Invalid HTTP header name: %r" % self.hdr


class UnsupportedTransferCoding(ParseException):
    def __init__(self, hdr):
        self.hdr = hdr
        self.code = 501

    def __str__(self):
        return "Unsupported transfer coding: %r" % self.hdr


class InvalidChunkSize(IOError):
    def __init__(self, data):
        self.data = data

    def __str__(self):
        return "Invalid chunk size: %r" % self.data


class ChunkMissingTerminator(IOError):
    def __init__(self, term):
        self.term = term

    def __str__(self):
        return "Invalid chunk terminator is not '\\r\\n': %r" % self.term


class LimitRequestLine(ParseException):
    def __init__(self, size, max_size):
        self.size = size
        self.max_size = max_size

    def __str__(self):
        return "Request Line is too large (%s > %s)" % (self.size, self.max_size)


class LimitRequestHeaders(ParseException):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class InvalidProxyLine(ParseException):
    def __init__(self, line):
        self.line = line
        self.code = 400

    def __str__(self):
        return "Invalid PROXY line: %r" % self.line


class ForbiddenProxyRequest(ParseException):
    def __init__(self, host):
        self.host = host
        self.code = 403

    def __str__(self):
        return "Proxy request from %r not allowed" % self.host


class InvalidSchemeHeaders(ParseException):
    def __str__(self):
        return "Contradictory scheme headers"
