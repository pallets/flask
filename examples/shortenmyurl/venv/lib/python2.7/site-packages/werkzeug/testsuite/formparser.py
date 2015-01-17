# -*- coding: utf-8 -*-
"""
    werkzeug.testsuite.formparser
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests the form parsing facilities.

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import with_statement

import unittest
from os.path import join, dirname

from werkzeug.testsuite import WerkzeugTestCase

from werkzeug import formparser
from werkzeug.test import create_environ, Client
from werkzeug.wrappers import Request, Response
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.datastructures import MultiDict
from werkzeug.formparser import parse_form_data
from werkzeug._compat import BytesIO


@Request.application
def form_data_consumer(request):
    result_object = request.args['object']
    if result_object == 'text':
        return Response(repr(request.form['text']))
    f = request.files[result_object]
    return Response(b'\n'.join((
        repr(f.filename).encode('ascii'),
        repr(f.name).encode('ascii'),
        repr(f.content_type).encode('ascii'),
        f.stream.read()
    )))


def get_contents(filename):
    with open(filename, 'rb') as f:
        return f.read()


class FormParserTestCase(WerkzeugTestCase):

    def test_limiting(self):
        data = b'foo=Hello+World&bar=baz'
        req = Request.from_values(input_stream=BytesIO(data),
                                  content_length=len(data),
                                  content_type='application/x-www-form-urlencoded',
                                  method='POST')
        req.max_content_length = 400
        self.assert_strict_equal(req.form['foo'], u'Hello World')

        req = Request.from_values(input_stream=BytesIO(data),
                                  content_length=len(data),
                                  content_type='application/x-www-form-urlencoded',
                                  method='POST')
        req.max_form_memory_size = 7
        self.assert_raises(RequestEntityTooLarge, lambda: req.form['foo'])

        req = Request.from_values(input_stream=BytesIO(data),
                                  content_length=len(data),
                                  content_type='application/x-www-form-urlencoded',
                                  method='POST')
        req.max_form_memory_size = 400
        self.assert_strict_equal(req.form['foo'], u'Hello World')

        data = (b'--foo\r\nContent-Disposition: form-field; name=foo\r\n\r\n'
                b'Hello World\r\n'
                b'--foo\r\nContent-Disposition: form-field; name=bar\r\n\r\n'
                b'bar=baz\r\n--foo--')
        req = Request.from_values(input_stream=BytesIO(data),
                                  content_length=len(data),
                                  content_type='multipart/form-data; boundary=foo',
                                  method='POST')
        req.max_content_length = 4
        self.assert_raises(RequestEntityTooLarge, lambda: req.form['foo'])

        req = Request.from_values(input_stream=BytesIO(data),
                                  content_length=len(data),
                                  content_type='multipart/form-data; boundary=foo',
                                  method='POST')
        req.max_content_length = 400
        self.assert_strict_equal(req.form['foo'], u'Hello World')

        req = Request.from_values(input_stream=BytesIO(data),
                                  content_length=len(data),
                                  content_type='multipart/form-data; boundary=foo',
                                  method='POST')
        req.max_form_memory_size = 7
        self.assert_raises(RequestEntityTooLarge, lambda: req.form['foo'])

        req = Request.from_values(input_stream=BytesIO(data),
                                  content_length=len(data),
                                  content_type='multipart/form-data; boundary=foo',
                                  method='POST')
        req.max_form_memory_size = 400
        self.assert_strict_equal(req.form['foo'], u'Hello World')

    def test_missing_multipart_boundary(self):
        data = (b'--foo\r\nContent-Disposition: form-field; name=foo\r\n\r\n'
                b'Hello World\r\n'
                b'--foo\r\nContent-Disposition: form-field; name=bar\r\n\r\n'
                b'bar=baz\r\n--foo--')
        req = Request.from_values(input_stream=BytesIO(data),
                                  content_length=len(data),
                                  content_type='multipart/form-data',
                                  method='POST')
        self.assert_equal(req.form, {})

    def test_parse_form_data_put_without_content(self):
        # A PUT without a Content-Type header returns empty data

        # Both rfc1945 and rfc2616 (1.0 and 1.1) say "Any HTTP/[1.0/1.1] message
        # containing an entity-body SHOULD include a Content-Type header field
        # defining the media type of that body."  In the case where either
        # headers are omitted, parse_form_data should still work.
        env = create_environ('/foo', 'http://example.org/', method='PUT')
        del env['CONTENT_TYPE']
        del env['CONTENT_LENGTH']

        stream, form, files = formparser.parse_form_data(env)
        self.assert_strict_equal(stream.read(), b'')
        self.assert_strict_equal(len(form), 0)
        self.assert_strict_equal(len(files), 0)

    def test_parse_form_data_get_without_content(self):
        env = create_environ('/foo', 'http://example.org/', method='GET')
        del env['CONTENT_TYPE']
        del env['CONTENT_LENGTH']

        stream, form, files = formparser.parse_form_data(env)
        self.assert_strict_equal(stream.read(), b'')
        self.assert_strict_equal(len(form), 0)
        self.assert_strict_equal(len(files), 0)

    def test_large_file(self):
        data = b'x' * (1024 * 600)
        req = Request.from_values(data={'foo': (BytesIO(data), 'test.txt')},
                                  method='POST')
        # make sure we have a real file here, because we expect to be
        # on the disk.  > 1024 * 500
        self.assert_true(hasattr(req.files['foo'].stream, u'fileno'))
        # close file to prevent fds from leaking
        req.files['foo'].close()

    def test_streaming_parse(self):
        data = b'x' * (1024 * 600)
        class StreamMPP(formparser.MultiPartParser):
            def parse(self, file, boundary, content_length):
                i = iter(self.parse_lines(file, boundary, content_length))
                one = next(i)
                two = next(i)
                return self.cls(()), {'one': one, 'two': two}
        class StreamFDP(formparser.FormDataParser):
            def _sf_parse_multipart(self, stream, mimetype,
                                    content_length, options):
                form, files = StreamMPP(
                    self.stream_factory, self.charset, self.errors,
                    max_form_memory_size=self.max_form_memory_size,
                    cls=self.cls).parse(stream, options.get('boundary').encode('ascii'),
                                        content_length)
                return stream, form, files
            parse_functions = {}
            parse_functions.update(formparser.FormDataParser.parse_functions)
            parse_functions['multipart/form-data'] = _sf_parse_multipart
        class StreamReq(Request):
            form_data_parser_class = StreamFDP
        req = StreamReq.from_values(data={'foo': (BytesIO(data), 'test.txt')},
                                    method='POST')
        self.assert_strict_equal('begin_file', req.files['one'][0])
        self.assert_strict_equal(('foo', 'test.txt'), req.files['one'][1][1:])
        self.assert_strict_equal('cont', req.files['two'][0])
        self.assert_strict_equal(data, req.files['two'][1])


class MultiPartTestCase(WerkzeugTestCase):

    def test_basic(self):
        resources = join(dirname(__file__), 'multipart')
        client = Client(form_data_consumer, Response)

        repository = [
            ('firefox3-2png1txt', '---------------------------186454651713519341951581030105', [
                (u'anchor.png', 'file1', 'image/png', 'file1.png'),
                (u'application_edit.png', 'file2', 'image/png', 'file2.png')
            ], u'example text'),
            ('firefox3-2pnglongtext', '---------------------------14904044739787191031754711748', [
                (u'accept.png', 'file1', 'image/png', 'file1.png'),
                (u'add.png', 'file2', 'image/png', 'file2.png')
            ], u'--long text\r\n--with boundary\r\n--lookalikes--'),
            ('opera8-2png1txt', '----------zEO9jQKmLc2Cq88c23Dx19', [
                (u'arrow_branch.png', 'file1', 'image/png', 'file1.png'),
                (u'award_star_bronze_1.png', 'file2', 'image/png', 'file2.png')
            ], u'blafasel öäü'),
            ('webkit3-2png1txt', '----WebKitFormBoundaryjdSFhcARk8fyGNy6', [
                (u'gtk-apply.png', 'file1', 'image/png', 'file1.png'),
                (u'gtk-no.png', 'file2', 'image/png', 'file2.png')
            ], u'this is another text with ümläüts'),
            ('ie6-2png1txt', '---------------------------7d91b03a20128', [
                (u'file1.png', 'file1', 'image/x-png', 'file1.png'),
                (u'file2.png', 'file2', 'image/x-png', 'file2.png')
            ], u'ie6 sucks :-/')
        ]

        for name, boundary, files, text in repository:
            folder = join(resources, name)
            data = get_contents(join(folder, 'request.txt'))
            for filename, field, content_type, fsname in files:
                response = client.post('/?object=' + field, data=data, content_type=
                                       'multipart/form-data; boundary="%s"' % boundary,
                                       content_length=len(data))
                lines = response.get_data().split(b'\n', 3)
                self.assert_strict_equal(lines[0], repr(filename).encode('ascii'))
                self.assert_strict_equal(lines[1], repr(field).encode('ascii'))
                self.assert_strict_equal(lines[2], repr(content_type).encode('ascii'))
                self.assert_strict_equal(lines[3], get_contents(join(folder, fsname)))
            response = client.post('/?object=text', data=data, content_type=
                                   'multipart/form-data; boundary="%s"' % boundary,
                                   content_length=len(data))
            self.assert_strict_equal(response.get_data(), repr(text).encode('utf-8'))

    def test_ie7_unc_path(self):
        client = Client(form_data_consumer, Response)
        data_file = join(dirname(__file__), 'multipart', 'ie7_full_path_request.txt')
        data = get_contents(data_file)
        boundary = '---------------------------7da36d1b4a0164'
        response = client.post('/?object=cb_file_upload_multiple', data=data, content_type=
                                   'multipart/form-data; boundary="%s"' % boundary, content_length=len(data))
        lines = response.get_data().split(b'\n', 3)
        self.assert_strict_equal(lines[0],
                          repr(u'Sellersburg Town Council Meeting 02-22-2010doc.doc').encode('ascii'))

    def test_end_of_file(self):
        # This test looks innocent but it was actually timeing out in
        # the Werkzeug 0.5 release version (#394)
        data = (
            b'--foo\r\n'
            b'Content-Disposition: form-data; name="test"; filename="test.txt"\r\n'
            b'Content-Type: text/plain\r\n\r\n'
            b'file contents and no end'
        )
        data = Request.from_values(input_stream=BytesIO(data),
                                   content_length=len(data),
                                   content_type='multipart/form-data; boundary=foo',
                                   method='POST')
        self.assert_true(not data.files)
        self.assert_true(not data.form)

    def test_broken(self):
        data = (
            '--foo\r\n'
            'Content-Disposition: form-data; name="test"; filename="test.txt"\r\n'
            'Content-Transfer-Encoding: base64\r\n'
            'Content-Type: text/plain\r\n\r\n'
            'broken base 64'
            '--foo--'
        )
        _, form, files = formparser.parse_form_data(create_environ(data=data,
            method='POST', content_type='multipart/form-data; boundary=foo'))
        self.assert_true(not files)
        self.assert_true(not form)

        self.assert_raises(ValueError, formparser.parse_form_data,
            create_environ(data=data, method='POST',
                      content_type='multipart/form-data; boundary=foo'),
                      silent=False)

    def test_file_no_content_type(self):
        data = (
            b'--foo\r\n'
            b'Content-Disposition: form-data; name="test"; filename="test.txt"\r\n\r\n'
            b'file contents\r\n--foo--'
        )
        data = Request.from_values(input_stream=BytesIO(data),
                                   content_length=len(data),
                                   content_type='multipart/form-data; boundary=foo',
                                   method='POST')
        self.assert_equal(data.files['test'].filename, 'test.txt')
        self.assert_strict_equal(data.files['test'].read(), b'file contents')

    def test_extra_newline(self):
        # this test looks innocent but it was actually timeing out in
        # the Werkzeug 0.5 release version (#394)
        data = (
            b'\r\n\r\n--foo\r\n'
            b'Content-Disposition: form-data; name="foo"\r\n\r\n'
            b'a string\r\n'
            b'--foo--'
        )
        data = Request.from_values(input_stream=BytesIO(data),
                                   content_length=len(data),
                                   content_type='multipart/form-data; boundary=foo',
                                   method='POST')
        self.assert_true(not data.files)
        self.assert_strict_equal(data.form['foo'], u'a string')

    def test_headers(self):
        data = (b'--foo\r\n'
                b'Content-Disposition: form-data; name="foo"; filename="foo.txt"\r\n'
                b'X-Custom-Header: blah\r\n'
                b'Content-Type: text/plain; charset=utf-8\r\n\r\n'
                b'file contents, just the contents\r\n'
                b'--foo--')
        req = Request.from_values(input_stream=BytesIO(data),
                                  content_length=len(data),
                                  content_type='multipart/form-data; boundary=foo',
                                  method='POST')
        foo = req.files['foo']
        self.assert_strict_equal(foo.mimetype, 'text/plain')
        self.assert_strict_equal(foo.mimetype_params, {'charset': 'utf-8'})
        self.assert_strict_equal(foo.headers['content-type'], foo.content_type)
        self.assert_strict_equal(foo.content_type, 'text/plain; charset=utf-8')
        self.assert_strict_equal(foo.headers['x-custom-header'], 'blah')

    def test_nonstandard_line_endings(self):
        for nl in b'\n', b'\r', b'\r\n':
            data = nl.join((
                b'--foo',
                b'Content-Disposition: form-data; name=foo',
                b'',
                b'this is just bar',
                b'--foo',
                b'Content-Disposition: form-data; name=bar',
                b'',
                b'blafasel',
                b'--foo--'
            ))
            req = Request.from_values(input_stream=BytesIO(data),
                                      content_length=len(data),
                                      content_type='multipart/form-data; '
                                      'boundary=foo', method='POST')
            self.assert_strict_equal(req.form['foo'], u'this is just bar')
            self.assert_strict_equal(req.form['bar'], u'blafasel')

    def test_failures(self):
        def parse_multipart(stream, boundary, content_length):
            parser = formparser.MultiPartParser(content_length)
            return parser.parse(stream, boundary, content_length)
        self.assert_raises(ValueError, parse_multipart, BytesIO(), b'broken  ', 0)

        data = b'--foo\r\n\r\nHello World\r\n--foo--'
        self.assert_raises(ValueError, parse_multipart, BytesIO(data), b'foo', len(data))

        data = b'--foo\r\nContent-Disposition: form-field; name=foo\r\n' \
               b'Content-Transfer-Encoding: base64\r\n\r\nHello World\r\n--foo--'
        self.assert_raises(ValueError, parse_multipart, BytesIO(data), b'foo', len(data))

        data = b'--foo\r\nContent-Disposition: form-field; name=foo\r\n\r\nHello World\r\n'
        self.assert_raises(ValueError, parse_multipart, BytesIO(data), b'foo', len(data))

        x = formparser.parse_multipart_headers(['foo: bar\r\n', ' x test\r\n'])
        self.assert_strict_equal(x['foo'], 'bar\n x test')
        self.assert_raises(ValueError, formparser.parse_multipart_headers,
                           ['foo: bar\r\n', ' x test'])

    def test_bad_newline_bad_newline_assumption(self):
        class ISORequest(Request):
            charset = 'latin1'
        contents = b'U2vlbmUgbORu'
        data = b'--foo\r\nContent-Disposition: form-data; name="test"\r\n' \
               b'Content-Transfer-Encoding: base64\r\n\r\n' + \
               contents + b'\r\n--foo--'
        req = ISORequest.from_values(input_stream=BytesIO(data),
                                     content_length=len(data),
                                     content_type='multipart/form-data; boundary=foo',
                                     method='POST')
        self.assert_strict_equal(req.form['test'], u'Sk\xe5ne l\xe4n')

    def test_empty_multipart(self):
        environ = {}
        data = b'--boundary--'
        environ['REQUEST_METHOD'] = 'POST'
        environ['CONTENT_TYPE'] = 'multipart/form-data; boundary=boundary'
        environ['CONTENT_LENGTH'] = str(len(data))
        environ['wsgi.input'] = BytesIO(data)
        stream, form, files = parse_form_data(environ, silent=False)
        rv = stream.read()
        self.assert_equal(rv, b'')
        self.assert_equal(form, MultiDict())
        self.assert_equal(files, MultiDict())


class InternalFunctionsTestCase(WerkzeugTestCase):

    def test_line_parser(self):
        assert formparser._line_parse('foo') == ('foo', False)
        assert formparser._line_parse('foo\r\n') == ('foo', True)
        assert formparser._line_parse('foo\r') == ('foo', True)
        assert formparser._line_parse('foo\n') == ('foo', True)

    def test_find_terminator(self):
        lineiter = iter(b'\n\n\nfoo\nbar\nbaz'.splitlines(True))
        find_terminator = formparser.MultiPartParser()._find_terminator
        line = find_terminator(lineiter)
        self.assert_equal(line, b'foo')
        self.assert_equal(list(lineiter), [b'bar\n', b'baz'])
        self.assert_equal(find_terminator([]), b'')
        self.assert_equal(find_terminator([b'']), b'')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(FormParserTestCase))
    suite.addTest(unittest.makeSuite(MultiPartTestCase))
    suite.addTest(unittest.makeSuite(InternalFunctionsTestCase))
    return suite
