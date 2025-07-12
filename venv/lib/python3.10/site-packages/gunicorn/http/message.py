#
# This file is part of gunicorn released under the MIT license.
# See the NOTICE for more information.

import io
import re
import socket

from gunicorn.http.body import ChunkedReader, LengthReader, EOFReader, Body
from gunicorn.http.errors import (
    InvalidHeader, InvalidHeaderName, NoMoreData,
    InvalidRequestLine, InvalidRequestMethod, InvalidHTTPVersion,
    LimitRequestLine, LimitRequestHeaders,
    UnsupportedTransferCoding, ObsoleteFolding,
)
from gunicorn.http.errors import InvalidProxyLine, ForbiddenProxyRequest
from gunicorn.http.errors import InvalidSchemeHeaders
from gunicorn.util import bytes_to_str, split_request_uri

MAX_REQUEST_LINE = 8190
MAX_HEADERS = 32768
DEFAULT_MAX_HEADERFIELD_SIZE = 8190

# verbosely on purpose, avoid backslash ambiguity
RFC9110_5_6_2_TOKEN_SPECIALS = r"!#$%&'*+-.^_`|~"
TOKEN_RE = re.compile(r"[%s0-9a-zA-Z]+" % (re.escape(RFC9110_5_6_2_TOKEN_SPECIALS)))
METHOD_BADCHAR_RE = re.compile("[a-z#]")
# usually 1.0 or 1.1 - RFC9112 permits restricting to single-digit versions
VERSION_RE = re.compile(r"HTTP/(\d)\.(\d)")
RFC9110_5_5_INVALID_AND_DANGEROUS = re.compile(r"[\0\r\n]")


class Message:
    def __init__(self, cfg, unreader, peer_addr):
        self.cfg = cfg
        self.unreader = unreader
        self.peer_addr = peer_addr
        self.remote_addr = peer_addr
        self.version = None
        self.headers = []
        self.trailers = []
        self.body = None
        self.scheme = "https" if cfg.is_ssl else "http"
        self.must_close = False

        # set headers limits
        self.limit_request_fields = cfg.limit_request_fields
        if (self.limit_request_fields <= 0
                or self.limit_request_fields > MAX_HEADERS):
            self.limit_request_fields = MAX_HEADERS
        self.limit_request_field_size = cfg.limit_request_field_size
        if self.limit_request_field_size < 0:
            self.limit_request_field_size = DEFAULT_MAX_HEADERFIELD_SIZE

        # set max header buffer size
        max_header_field_size = self.limit_request_field_size or DEFAULT_MAX_HEADERFIELD_SIZE
        self.max_buffer_headers = self.limit_request_fields * \
            (max_header_field_size + 2) + 4

        unused = self.parse(self.unreader)
        self.unreader.unread(unused)
        self.set_body_reader()

    def force_close(self):
        self.must_close = True

    def parse(self, unreader):
        raise NotImplementedError()

    def parse_headers(self, data, from_trailer=False):
        cfg = self.cfg
        headers = []

        # Split lines on \r\n
        lines = [bytes_to_str(line) for line in data.split(b"\r\n")]

        # handle scheme headers
        scheme_header = False
        secure_scheme_headers = {}
        forwarder_headers = []
        if from_trailer:
            # nonsense. either a request is https from the beginning
            #  .. or we are just behind a proxy who does not remove conflicting trailers
            pass
        elif ('*' in cfg.forwarded_allow_ips or
              not isinstance(self.peer_addr, tuple)
              or self.peer_addr[0] in cfg.forwarded_allow_ips):
            secure_scheme_headers = cfg.secure_scheme_headers
            forwarder_headers = cfg.forwarder_headers

        # Parse headers into key/value pairs paying attention
        # to continuation lines.
        while lines:
            if len(headers) >= self.limit_request_fields:
                raise LimitRequestHeaders("limit request headers fields")

            # Parse initial header name: value pair.
            curr = lines.pop(0)
            header_length = len(curr) + len("\r\n")
            if curr.find(":") <= 0:
                raise InvalidHeader(curr)
            name, value = curr.split(":", 1)
            if self.cfg.strip_header_spaces:
                name = name.rstrip(" \t")
            if not TOKEN_RE.fullmatch(name):
                raise InvalidHeaderName(name)

            # this is still a dangerous place to do this
            #  but it is more correct than doing it before the pattern match:
            # after we entered Unicode wonderland, 8bits could case-shift into ASCII:
            # b"\xDF".decode("latin-1").upper().encode("ascii") == b"SS"
            name = name.upper()

            value = [value.strip(" \t")]

            # Consume value continuation lines..
            while lines and lines[0].startswith((" ", "\t")):
                # .. which is obsolete here, and no longer done by default
                if not self.cfg.permit_obsolete_folding:
                    raise ObsoleteFolding(name)
                curr = lines.pop(0)
                header_length += len(curr) + len("\r\n")
                if header_length > self.limit_request_field_size > 0:
                    raise LimitRequestHeaders("limit request headers "
                                              "fields size")
                value.append(curr.strip("\t "))
            value = " ".join(value)

            if RFC9110_5_5_INVALID_AND_DANGEROUS.search(value):
                raise InvalidHeader(name)

            if header_length > self.limit_request_field_size > 0:
                raise LimitRequestHeaders("limit request headers fields size")

            if name in secure_scheme_headers:
                secure = value == secure_scheme_headers[name]
                scheme = "https" if secure else "http"
                if scheme_header:
                    if scheme != self.scheme:
                        raise InvalidSchemeHeaders()
                else:
                    scheme_header = True
                    self.scheme = scheme

            # ambiguous mapping allows fooling downstream, e.g. merging non-identical headers:
            # X-Forwarded-For: 2001:db8::ha:cc:ed
            # X_Forwarded_For: 127.0.0.1,::1
            # HTTP_X_FORWARDED_FOR = 2001:db8::ha:cc:ed,127.0.0.1,::1
            # Only modify after fixing *ALL* header transformations; network to wsgi env
            if "_" in name:
                if name in forwarder_headers or "*" in forwarder_headers:
                    # This forwarder may override our environment
                    pass
                elif self.cfg.header_map == "dangerous":
                    # as if we did not know we cannot safely map this
                    pass
                elif self.cfg.header_map == "drop":
                    # almost as if it never had been there
                    # but still counts against resource limits
                    continue
                else:
                    # fail-safe fallthrough: refuse
                    raise InvalidHeaderName(name)

            headers.append((name, value))

        return headers

    def set_body_reader(self):
        chunked = False
        content_length = None

        for (name, value) in self.headers:
            if name == "CONTENT-LENGTH":
                if content_length is not None:
                    raise InvalidHeader("CONTENT-LENGTH", req=self)
                content_length = value
            elif name == "TRANSFER-ENCODING":
                # T-E can be a list
                # https://datatracker.ietf.org/doc/html/rfc9112#name-transfer-encoding
                vals = [v.strip() for v in value.split(',')]
                for val in vals:
                    if val.lower() == "chunked":
                        # DANGER: transfer codings stack, and stacked chunking is never intended
                        if chunked:
                            raise InvalidHeader("TRANSFER-ENCODING", req=self)
                        chunked = True
                    elif val.lower() == "identity":
                        # does not do much, could still plausibly desync from what the proxy does
                        # safe option: nuke it, its never needed
                        if chunked:
                            raise InvalidHeader("TRANSFER-ENCODING", req=self)
                    elif val.lower() in ('compress', 'deflate', 'gzip'):
                        # chunked should be the last one
                        if chunked:
                            raise InvalidHeader("TRANSFER-ENCODING", req=self)
                        self.force_close()
                    else:
                        raise UnsupportedTransferCoding(value)

        if chunked:
            # two potentially dangerous cases:
            #  a) CL + TE (TE overrides CL.. only safe if the recipient sees it that way too)
            #  b) chunked HTTP/1.0 (always faulty)
            if self.version < (1, 1):
                # framing wonky, see RFC 9112 Section 6.1
                raise InvalidHeader("TRANSFER-ENCODING", req=self)
            if content_length is not None:
                # we cannot be certain the message framing we understood matches proxy intent
                #  -> whatever happens next, remaining input must not be trusted
                raise InvalidHeader("CONTENT-LENGTH", req=self)
            self.body = Body(ChunkedReader(self, self.unreader))
        elif content_length is not None:
            try:
                if str(content_length).isnumeric():
                    content_length = int(content_length)
                else:
                    raise InvalidHeader("CONTENT-LENGTH", req=self)
            except ValueError:
                raise InvalidHeader("CONTENT-LENGTH", req=self)

            if content_length < 0:
                raise InvalidHeader("CONTENT-LENGTH", req=self)

            self.body = Body(LengthReader(self.unreader, content_length))
        else:
            self.body = Body(EOFReader(self.unreader))

    def should_close(self):
        if self.must_close:
            return True
        for (h, v) in self.headers:
            if h == "CONNECTION":
                v = v.lower().strip(" \t")
                if v == "close":
                    return True
                elif v == "keep-alive":
                    return False
                break
        return self.version <= (1, 0)


class Request(Message):
    def __init__(self, cfg, unreader, peer_addr, req_number=1):
        self.method = None
        self.uri = None
        self.path = None
        self.query = None
        self.fragment = None

        # get max request line size
        self.limit_request_line = cfg.limit_request_line
        if (self.limit_request_line < 0
                or self.limit_request_line >= MAX_REQUEST_LINE):
            self.limit_request_line = MAX_REQUEST_LINE

        self.req_number = req_number
        self.proxy_protocol_info = None
        super().__init__(cfg, unreader, peer_addr)

    def get_data(self, unreader, buf, stop=False):
        data = unreader.read()
        if not data:
            if stop:
                raise StopIteration()
            raise NoMoreData(buf.getvalue())
        buf.write(data)

    def parse(self, unreader):
        buf = io.BytesIO()
        self.get_data(unreader, buf, stop=True)

        # get request line
        line, rbuf = self.read_line(unreader, buf, self.limit_request_line)

        # proxy protocol
        if self.proxy_protocol(bytes_to_str(line)):
            # get next request line
            buf = io.BytesIO()
            buf.write(rbuf)
            line, rbuf = self.read_line(unreader, buf, self.limit_request_line)

        self.parse_request_line(line)
        buf = io.BytesIO()
        buf.write(rbuf)

        # Headers
        data = buf.getvalue()
        idx = data.find(b"\r\n\r\n")

        done = data[:2] == b"\r\n"
        while True:
            idx = data.find(b"\r\n\r\n")
            done = data[:2] == b"\r\n"

            if idx < 0 and not done:
                self.get_data(unreader, buf)
                data = buf.getvalue()
                if len(data) > self.max_buffer_headers:
                    raise LimitRequestHeaders("max buffer headers")
            else:
                break

        if done:
            self.unreader.unread(data[2:])
            return b""

        self.headers = self.parse_headers(data[:idx], from_trailer=False)

        ret = data[idx + 4:]
        buf = None
        return ret

    def read_line(self, unreader, buf, limit=0):
        data = buf.getvalue()

        while True:
            idx = data.find(b"\r\n")
            if idx >= 0:
                # check if the request line is too large
                if idx > limit > 0:
                    raise LimitRequestLine(idx, limit)
                break
            if len(data) - 2 > limit > 0:
                raise LimitRequestLine(len(data), limit)
            self.get_data(unreader, buf)
            data = buf.getvalue()

        return (data[:idx],  # request line,
                data[idx + 2:])  # residue in the buffer, skip \r\n

    def proxy_protocol(self, line):
        """\
        Detect, check and parse proxy protocol.

        :raises: ForbiddenProxyRequest, InvalidProxyLine.
        :return: True for proxy protocol line else False
        """
        if not self.cfg.proxy_protocol:
            return False

        if self.req_number != 1:
            return False

        if not line.startswith("PROXY"):
            return False

        self.proxy_protocol_access_check()
        self.parse_proxy_protocol(line)

        return True

    def proxy_protocol_access_check(self):
        # check in allow list
        if ("*" not in self.cfg.proxy_allow_ips and
            isinstance(self.peer_addr, tuple) and
                self.peer_addr[0] not in self.cfg.proxy_allow_ips):
            raise ForbiddenProxyRequest(self.peer_addr[0])

    def parse_proxy_protocol(self, line):
        bits = line.split(" ")

        if len(bits) != 6:
            raise InvalidProxyLine(line)

        # Extract data
        proto = bits[1]
        s_addr = bits[2]
        d_addr = bits[3]

        # Validation
        if proto not in ["TCP4", "TCP6"]:
            raise InvalidProxyLine("protocol '%s' not supported" % proto)
        if proto == "TCP4":
            try:
                socket.inet_pton(socket.AF_INET, s_addr)
                socket.inet_pton(socket.AF_INET, d_addr)
            except OSError:
                raise InvalidProxyLine(line)
        elif proto == "TCP6":
            try:
                socket.inet_pton(socket.AF_INET6, s_addr)
                socket.inet_pton(socket.AF_INET6, d_addr)
            except OSError:
                raise InvalidProxyLine(line)

        try:
            s_port = int(bits[4])
            d_port = int(bits[5])
        except ValueError:
            raise InvalidProxyLine("invalid port %s" % line)

        if not ((0 <= s_port <= 65535) and (0 <= d_port <= 65535)):
            raise InvalidProxyLine("invalid port %s" % line)

        # Set data
        self.proxy_protocol_info = {
            "proxy_protocol": proto,
            "client_addr": s_addr,
            "client_port": s_port,
            "proxy_addr": d_addr,
            "proxy_port": d_port
        }

    def parse_request_line(self, line_bytes):
        bits = [bytes_to_str(bit) for bit in line_bytes.split(b" ", 2)]
        if len(bits) != 3:
            raise InvalidRequestLine(bytes_to_str(line_bytes))

        # Method: RFC9110 Section 9
        self.method = bits[0]

        # nonstandard restriction, suitable for all IANA registered methods
        # partially enforced in previous gunicorn versions
        if not self.cfg.permit_unconventional_http_method:
            if METHOD_BADCHAR_RE.search(self.method):
                raise InvalidRequestMethod(self.method)
            if not 3 <= len(bits[0]) <= 20:
                raise InvalidRequestMethod(self.method)
        # standard restriction: RFC9110 token
        if not TOKEN_RE.fullmatch(self.method):
            raise InvalidRequestMethod(self.method)
        # nonstandard and dangerous
        # methods are merely uppercase by convention, no case-insensitive treatment is intended
        if self.cfg.casefold_http_method:
            self.method = self.method.upper()

        # URI
        self.uri = bits[1]

        # Python stdlib explicitly tells us it will not perform validation.
        # https://docs.python.org/3/library/urllib.parse.html#url-parsing-security
        # There are *four* `request-target` forms in rfc9112, none of them can be empty:
        # 1. origin-form, which starts with a slash
        # 2. absolute-form, which starts with a non-empty scheme
        # 3. authority-form, (for CONNECT) which contains a colon after the host
        # 4. asterisk-form, which is an asterisk (`\x2A`)
        # => manually reject one always invalid URI: empty
        if len(self.uri) == 0:
            raise InvalidRequestLine(bytes_to_str(line_bytes))

        try:
            parts = split_request_uri(self.uri)
        except ValueError:
            raise InvalidRequestLine(bytes_to_str(line_bytes))
        self.path = parts.path or ""
        self.query = parts.query or ""
        self.fragment = parts.fragment or ""

        # Version
        match = VERSION_RE.fullmatch(bits[2])
        if match is None:
            raise InvalidHTTPVersion(bits[2])
        self.version = (int(match.group(1)), int(match.group(2)))
        if not (1, 0) <= self.version < (2, 0):
            # if ever relaxing this, carefully review Content-Encoding processing
            if not self.cfg.permit_unconventional_http_version:
                raise InvalidHTTPVersion(self.version)

    def set_body_reader(self):
        super().set_body_reader()
        if isinstance(self.body.reader, EOFReader):
            self.body = Body(LengthReader(self.unreader, 0))
