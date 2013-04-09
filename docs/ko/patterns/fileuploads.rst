.. _uploading-files:

파일 업로드하기
===============

오 그렇다, 그리운 파일 업로드이다.  파일 업로드의 기본 방식은
실제로 굉장히 간단하다.  기본적으로 다음과 같이 동작한다:

1. ``<form>`` 태그에 ``enctype=multipart/form-data`` 과 ``<input type=file>`` 
   을 넣는다.
2. 어플리케이션이 요청 객체에 :attr:`~flask.request.files` 딕셔너리로 부터 파일 객체에
   접근한다.
3. 파일시스템에 영구적으로 저장하기 위해 파일 객체의 
   :meth:`~werkzeug.datastructures.FileStorage.save` 메소드를 사용한다.

파일 업로드의 가벼운 소개
-------------------------

지정된 업로드 폴더에 파일을 업로드하고 사용자에게 파일을 보여주는 매우
간단한 어플리케이션으로 시작해보자::

    import os
    from flask import Flask, request, redirect, url_for
    from werkzeug import secure_filename

    UPLOAD_FOLDER = '/path/to/the/uploads'
    ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

자 첫번째로 몇 가지 패키지를 임포트해야한다.  대부분 직관적이지만,
:func:`werkzeug.secure_filename` 은 나중에 약간 설명이 더 필요하다.
`UPLOAD_FOLDER` 는 업로드된 파일이 저장되는 것이고 `ALLOWED_EXTENSIONS` 은
허용할 파일의 확장자들이다.  그리고 나면 보통은 어플리케이션에 직접 URL 
규칙을 추가하는데 여기서는 그렇게 하지 않을 것이다.  왜 여기서는 하지 않는가?
왜냐하면 우리가 사용하는 웹서버 (또는 개발 서버) 가 이런 파일을 업로드하는 
역할도 하기 때문에 이 파일에 대한 URL을 생성하기 위한 규칙만 필요로 한다.

Why do we limit the extensions that are allowed?  You probably don't want
your users to be able to upload everything there if the server is directly
sending out the data to the client.  That way you can make sure that users
are not able to upload HTML files that would cause XSS problems (see
:ref:`xss`).  Also make sure to disallow `.php` files if the server
executes them, but who has PHP installed on his server, right?  :)

Next the functions that check if an extension is valid and that uploads
the file and redirects the user to the URL for the uploaded file::

    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

    @app.route('/', methods=['GET', 'POST'])
    def upload_file():
        if request.method == 'POST':
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                return redirect(url_for('uploaded_file',
                                        filename=filename))
        return '''
        <!doctype html>
        <title>Upload new File</title>
        <h1>Upload new File</h1>
        <form action="" method=post enctype=multipart/form-data>
          <p><input type=file name=file>
             <input type=submit value=Upload>
        </form>
        '''

So what does that :func:`~werkzeug.utils.secure_filename` function actually do?
Now the problem is that there is that principle called "never trust user
input".  This is also true for the filename of an uploaded file.  All
submitted form data can be forged, and filenames can be dangerous.  For
the moment just remember: always use that function to secure a filename
before storing it directly on the filesystem.

.. admonition:: Information for the Pros

   So you're interested in what that :func:`~werkzeug.utils.secure_filename`
   function does and what the problem is if you're not using it?  So just
   imagine someone would send the following information as `filename` to
   your application::

      filename = "../../../../home/username/.bashrc"

   Assuming the number of ``../`` is correct and you would join this with
   the `UPLOAD_FOLDER` the user might have the ability to modify a file on
   the server's filesystem he or she should not modify.  This does require some
   knowledge about how the application looks like, but trust me, hackers
   are patient :)

   Now let's look how that function works:

   >>> secure_filename('../../../../home/username/.bashrc')
   'home_username_.bashrc'

Now one last thing is missing: the serving of the uploaded files.  As of
Flask 0.5 we can use a function that does that for us::

    from flask import send_from_directory

    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'],
                                   filename)

Alternatively you can register `uploaded_file` as `build_only` rule and
use the :class:`~werkzeug.wsgi.SharedDataMiddleware`.  This also works with
older versions of Flask::

    from werkzeug import SharedDataMiddleware
    app.add_url_rule('/uploads/<filename>', 'uploaded_file',
                     build_only=True)
    app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
        '/uploads':  app.config['UPLOAD_FOLDER']
    })

If you now run the application everything should work as expected.


Improving Uploads
-----------------

.. versionadded:: 0.6

So how exactly does Flask handle uploads?  Well it will store them in the
webserver's memory if the files are reasonable small otherwise in a
temporary location (as returned by :func:`tempfile.gettempdir`).  But how
do you specify the maximum file size after which an upload is aborted?  By
default Flask will happily accept file uploads to an unlimited amount of
memory, but you can limit that by setting the ``MAX_CONTENT_LENGTH``
config key::

    from flask import Flask, Request

    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

The code above will limited the maximum allowed payload to 16 megabytes.
If a larger file is transmitted, Flask will raise an
:exc:`~werkzeug.exceptions.RequestEntityTooLarge` exception.

This feature was added in Flask 0.6 but can be achieved in older versions
as well by subclassing the request object.  For more information on that
consult the Werkzeug documentation on file handling.


Upload Progress Bars
--------------------

A while ago many developers had the idea to read the incoming file in
small chunks and store the upload progress in the database to be able to
poll the progress with JavaScript from the client.  Long story short: the
client asks the server every 5 seconds how much it has transmitted
already.  Do you realize the irony?  The client is asking for something it
should already know.

Now there are better solutions to that work faster and more reliable.  The
web changed a lot lately and you can use HTML5, Java, Silverlight or Flash
to get a nicer uploading experience on the client side.  Look at the
following libraries for some nice examples how to do that:

-   `Plupload <http://www.plupload.com/>`_ - HTML5, Java, Flash
-   `SWFUpload <http://www.swfupload.org/>`_ - Flash
-   `JumpLoader <http://jumploader.com/>`_ - Java


An Easier Solution
------------------

Because the common pattern for file uploads exists almost unchanged in all
applications dealing with uploads, there is a Flask extension called
`Flask-Uploads`_ that implements a full fledged upload mechanism with
white and blacklisting of extensions and more.

.. _Flask-Uploads: http://packages.python.org/Flask-Uploads/
