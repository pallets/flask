Request Content Checksums
=========================

Various pieces of code can consume the request data and preprocess it.
For instance JSON data ends up on the request object already read and
processed, form data ends up there as well but goes through a different
code path.  This seems inconvenient when you want to calculate the
checksum of the incoming request data.  This is necessary sometimes for
some APIs.

Fortunately this is however very simple to change by wrapping the input
stream.

The following example calculates the SHA1 checksum of the incoming data as
it gets read and stores it in the WSGI environment::

    import hashlib

    class ChecksumCalcStream(object):

        def __init__(self, stream):
            self._stream = stream
            self._hash = hashlib.sha1()

        def read(self, bytes):
            rv = self._stream.read(bytes)
            self._hash.update(rv)
            return rv

        def readline(self, size_hint):
            rv = self._stream.readline(size_hint)
            self._hash.update(rv)
            return rv

    def generate_checksum(request):
        env = request.environ
        stream = ChecksumCalcStream(env['wsgi.input'])
        env['wsgi.input'] = stream
        return stream._hash

To use this, all you need to do is to hook the calculating stream in
before the request starts consuming data.  (Eg: be careful accessing
``request.form`` or anything of that nature.  ``before_request_handlers``
for instance should be careful not to access it).

Example usage::

    @app.route('/special-api', methods=['POST'])
    def special_api():
        hash = generate_checksum(request)
        # Accessing this parses the input stream
        files = request.files
        # At this point the hash is fully constructed.
        checksum = hash.hexdigest()
        return f"Hash was: {checksum}"
