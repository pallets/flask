# -*- coding: utf-8 -*-
"""
    flask.debughelpers
    ~~~~~~~~~~~~~~~~~~

    Various helpers to make the development experience better.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""


class DebugFilesKeyError(KeyError, AssertionError):
    """Raised from request.files during debugging.  The idea is that it can
    provide a better error message than just a generic KeyError/BadRequest.
    """

    def __init__(self, request, key):
        form_matches = request.form.getlist(key)
        buf = ['You tried to access the file "%s" in the request.files '
               'dictionary but it does not exist.  The mimetype for the request '
               'is "%s" instead of "multipart/form-data" which means that no '
               'file contents were transmitted.  To fix this error you should '
               'provide enctype="multipart/form-data" in your form.' %
               (key, request.mimetype)]
        if form_matches:
            buf.append('\n\nThe browser instead transmitted some file names. '
                       'This was submitted: %s' % ', '.join('"%s"' % x
                            for x in form_matches))
        self.msg = ''.join(buf).encode('utf-8')

    def __str__(self):
        return self.msg


def make_enctype_error_multidict(request):
    """Since Flask 0.8 we're monkeypatching the files object in case a
    request is detected that does not use multipart form data but the files
    object is accessed.
    """
    oldcls = request.files.__class__
    class newcls(oldcls):
        def __getitem__(self, key):
            try:
                return oldcls.__getitem__(self, key)
            except KeyError, e:
                if key not in request.form:
                    raise
                raise DebugFilesKeyError(request, key)
    newcls.__name__ = oldcls.__name__
    newcls.__module__ = oldcls.__module__
    request.files.__class__ = newcls
