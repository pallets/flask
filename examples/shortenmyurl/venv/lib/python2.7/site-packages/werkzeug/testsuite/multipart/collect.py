#!/usr/bin/env python
"""
Hacky helper application to collect form data.
"""
from werkzeug.serving import run_simple
from werkzeug.wrappers import Request, Response


def copy_stream(request):
    from os import mkdir
    from time import time
    folder = 'request-%d' % time()
    mkdir(folder)
    environ = request.environ
    f = open(folder + '/request.txt', 'wb+')
    f.write(environ['wsgi.input'].read(int(environ['CONTENT_LENGTH'])))
    f.flush()
    f.seek(0)
    environ['wsgi.input'] = f
    request.stat_folder = folder


def stats(request):
    copy_stream(request)
    f1 = request.files['file1']
    f2 = request.files['file2']
    text = request.form['text']
    f1.save(request.stat_folder + '/file1.bin')
    f2.save(request.stat_folder + '/file2.bin')
    open(request.stat_folder + '/text.txt', 'w').write(text.encode('utf-8'))
    return Response('Done.')


def upload_file(request):
    return Response('''
    <h1>Upload File</h1>
    <form action="" method="post" enctype="multipart/form-data">
        <input type="file" name="file1"><br>
        <input type="file" name="file2"><br>
        <textarea name="text"></textarea><br>
        <input type="submit" value="Send">
    </form>
    ''', mimetype='text/html')


def application(environ, start_responseonse):
    request = Request(environ)
    if request.method == 'POST':
        response = stats(request)
    else:
        response = upload_file(request)
    return response(environ, start_responseonse)


if __name__ == '__main__':
    run_simple('localhost', 5000, application, use_debugger=True)
