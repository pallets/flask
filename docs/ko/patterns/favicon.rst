파비콘 추가하기
===============

"파비콘(favicon)"은 탭이나 북마크를 위해 브라우저에서 사용되는 아이콘이다.
이 아이콘은 여러분의 웹사이트를 구분하는데 도움을 주고 그 사이트에 유일한 
표식을 준다.

일반적인 질문은 플라스크 어플리케이션에 어떻게 파이콘을 추가하는가 이다.
물론 제일 먼저 파이콘이 필요하다.  16 × 16 픽셀과 ICO 파일 형태이어야 한다.
이것은 전제사항은 아니지만 그 형태가 모든 브라우저에서 지원하는 업계 표준이다.
여러분의 static 디렉토리에 그 아이콘을 :file:`favicon.ico` 파일명으로 넣는다.

자, 그 아이콘을 브라우저에서 찾으려면, 여러분의 HTML에 link 태그를 추가하는게
알맞은 방법이다. 그래서 예를 들면:

.. sourcecode:: html+jinja

    <link rel="shortcut icon" href="{{ url_for('static', filename='favicon.ico') }}">

대부분의 브라우저에서는 위의 한줄이 여러분이 해줄 전부이지만, 몇몇 예전 브라우저는
이 표준을 지원하지 않는다.  예전 업계 표준은 웹사이트의 루트에 그 파일을 위치시켜
제공하는 것이다.  여러분의 어플리케이션이 해당 도메인의 루트 경로에 마운트되지
않았다면 루트에서 그 아이콘이 제공되도록 웹서버 설정이 필요하므로 그렇게 할 수
없다면 여러분은 운이 없는 것이다.  그러나 어프리케이션이 루트에 있다면 여러분은 
리디렉션으로 간단히 경로를 찾게할 수 있다::

    app.add_url_rule('/favicon.ico',
                     redirect_to=url_for('static', filename='favicon.ico'))

여러분이 추가적인 리디렉션 요청을 저장하고 싶다면 :func:`~flask.send_from_directory`
를 사용한 뷰 함수 또한 작성할 수 있다::

    import os
    from flask import send_from_directory

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'),
                                   'favicon.ico', mimetype='image/vnd.microsoft.icon')

명시적인 마임타입(mimetype)을 생략할 수 있고 그 타입은 추측될 것이지만, 그것은 
항상 같게 추측될 것이므로 추가적인 추측을 피하기 위해 타입을 지정하는 것이 좋다.

위의 예는 어플리케이션을 통해 아이콘을 제공할 것이고 가능하다면 웹서버 문서를
참고하여 그렇게 할 전담 웹서버를 구성하는 것이 더 좋다.

추가로 볼 내용
--------------

* 위키피디아(Wikipedia)의 `파비콘 <http://en.wikipedia.org/wiki/Favicon>`_ 기사
