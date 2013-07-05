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

왜 허용할 파일 확장자를 제한하는가?  서버가 클라이언트로 직접 데이타를 전송한다면
여러분은 아마도 사용자가 그 서버에 뭐든지 올릴 수 있는 것을 원하지 않을 것이다.
그런 방식으로 여러분은 사용자가 XSS 문제 (:ref:`xss`) 를 야기할 수도 있는
HTML 파일을 업로드하지 못하도록 할 수 있다.  또한 서버가 `.php` 파일과 같은 
스크립트를 실행할 수 있다면 그 파일 또한 허용하지 말아야 한다. 하지만, 누가
이 서버에 PHP를 설치하겠는가, 그렇지 않은가?  :)

다음은 확장자가 유효한지 확인하고 파일을 업로드하고 업로드된 파일에 대한 URL로
사용자를 리디렉션하는 함수들이다::

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

그렇다면 이 :func:`~werkzeug.utils.secure_filename` 함수는 실제로 무엇을 하는건가?
이제 문제는 "절대로 사용자의 입력을 믿지마라" 라고 불리우는 원칙에 있다.
이것은 또한 업로드된 파일명에 대해서도 적용된다. 모든 전송된 폼 데이타는
위조될 수 있고, 그래서 파일명이 위험할 수도 있다.  잠시동안 기억해보자:
파일시스템에 직접 파일을 저장하기 전에 파일명을 보호하기 위해 항상 이 함수를
사용하자.

.. admonition:: Information for the Pros 장점에 대한 정보

   그래서 여러분은 :func:`~werkzeug.utils.secure_filename` 함수가 하는 것에 
   관심이 있고 그 함수를 사용하지 않는다면 무슨 문제가 있는가?  그렇다면 어떤 사람이
   여러분의 어플리케이션에 `filename`으로 다음과 같은 정보를 보낸다고 생각해보자::

      filename = "../../../../home/username/.bashrc"

   ``../`` 의 개수가 맞게 되있고 이것과 `UPLOAD_FOLDER` 와 더한다고 가정하면
   사용자는 수정하면 않아야하는 서버의 파일시스템에 있는 파일을 수정할 수 있게
   된다.  이것은 어플리케이션이 어떻게 생겼는가에 대한 약간의 정보를 요구하지만,
   나를 믿어라, 해커들은 참을성이 많다 :)

   이제 이 함수가 동작하는 것을 살펴보자:

   >>> secure_filename('../../../../home/username/.bashrc')
   'home_username_.bashrc'

지금 한가지 마지막으로 놓친것이 있다: 업로드된 파일의 제공. 플라스크 0.5에
관해서 우리는 업로드된 파일을 받을 수 있는 함수를 사용할 수 있다::

    from flask import send_from_directory

    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'],
                                   filename)

다른방법으로 여러분은 `build_only` 로써 `uploaded_file` 을 등록하고 
:class:`~werkzeug.wsgi.SharedDataMiddleware` 를 사용할 수 있다.  이것은
또한 플라스크의 지난 과거 버전에서도 동작한다::

    from werkzeug import SharedDataMiddleware
    app.add_url_rule('/uploads/<filename>', 'uploaded_file',
                     build_only=True)
    app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
        '/uploads':  app.config['UPLOAD_FOLDER']
    })

여러분 이제 이 어플리케이션을 실행하면 기대하는데로 모든 것이 동작해야
할 것이다.


업로드 개선하기
---------------

.. versionadded:: 0.6

그렇다면 정확히 플라스크가 업로드를 어떻게 처리한다는 것인가?  플라스크는
업로드된 파일이 적당히 작다면 웹서버의 메모리에 저장하고 그렇지 않다면
웹서버의 임시 장소 (:func:`tempfile.gettempdir`) 저장할 것이다.  그러나
여러분은 어떻게 업로드를 중단된 후에 최대 파일 크기를 지정할 수 있는가?
기본으로 플라스크는 제한되지 않은 메모리까지 파일 업로드를 허용할 것이지만,
여러분은 ``MAX_CONTENT_LENGTH`` 설정 키값을 설정하여 크기를 제한할 수 있다::

    from flask import Flask, Request

    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

위의 코드는 허용되는 최대 파일 크기를 16메가바이트로 제한할 것이다.
그 최대 크기보다 더 큰 파일이 업로드되면, 플라스크는
:exc:`~werkzeug.exceptions.RequestEntityTooLarge` 예외를 발생시킬 것이다.

이 기능은 플라스크 0.6에서 추가됐지만, 요청 객체를 상속받아서 이전 버전에서
사용할 수도 있다.  더 많은 정보는 벡자이크(Werkzeug) 문서의 파일 처리(file handling)
을 검토해봐라.


업로드 진행 상태바 
------------------

얼마전에 많은 개발자들이 클라이언트에서 자바스크립트로 업로드 진행 상태를 
받아올 수 있도록 작은 단위로 유입되는 파일을 읽어서 데이터베이스에 진행 상태를 
저장하는 방식을 생각했다.  짧게 얘기하자면: 클라이언트가 서버에 5초마다 얼마나
전송됐는지 묻는다.  얼마나 아이러니인지 알겠는가?  클리언트는 이미 자신이 알고
있는 사실을 묻고 있는 것이다.

이제 더 빠르고 안정적으로 동작하는 더 좋은 해결책이 있다.  웹은 최근에 많은
변화가 있었고 여러분은 HTML5, Java, Silverlight 나 Flash 을 사용해서 클라이언트에서
더 좋은 업로드 경험을 얻을 수 있다.  다음 라이브러리들은 그런 작업을 할 수 있는
몇 가지 좋은 예제들을 보여준다:

-   `Plupload <http://www.plupload.com/>`_ - HTML5, Java, Flash
-   `SWFUpload <http://www.swfupload.org/>`_ - Flash
-   `JumpLoader <http://jumploader.com/>`_ - Java


더 쉬운 해결책
--------------

업로드를 다루는 모든 어플리케이션에서 파일 업로드에 대한 일반적인 패턴은 
거의 변화가 없었기 때문에, 파일 확장자에 대한 화이트/블랙리스트와 다른 많은 기능을
제공하는 업로드 메커니즘을 구현한 `Flask-Uploads`_ 라는 플라스크 확장이 있다.

.. _Flask-Uploads: http://packages.python.org/Flask-Uploads/
