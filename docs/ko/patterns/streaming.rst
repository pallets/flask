컨텐트 스트리밍하기
=====================

종종 여러분은 클라이언트로 메모리에 유지하고 싶은 양보다 훨씬 더 큰, 
엄청난 양의 데이터를 전송하기를 원한다.  여러분이 그 데이터를 바로 생성하고 
있을 때, 파일시스템으로 갔다오지 않고 어떻게 클라이언트로 그것을 전송하는가?

답은 바로 생성기(generators)와 직접 응답이다.

기본 사용법
-----------

이것은 많은 CSV 데이터를 즉각 생성하는 기초적인 뷰 함수이다.  데이터를 생성하는
생성기를 사용하는 내부(inner) 함수를 갖고 그 함수를 호출하면서 응답 객체에
그 함수를 넘기는것이 그 기법이다::

    from flask import Response

    @app.route('/large.csv')
    def generate_large_csv():
        def generate():
            for row in iter_all_rows():
                yield ','.join(row) + '\n'
        return Response(generate(), mimetype='text/csv')

각 ``yield`` 표현식은 브라우져에 직접 전송된다.  어떤 WSGI 미들웨어는 
스트리밍을 깰수도 있지만, 프로파일러를 가진 디버그 환경과 여러분이 활성화
시킨 다른 것들을 조심하도록 유의하라.

템플릿에서 스트리밍
-------------------

진자2 템플릿 엔진은 또한 부분 단위로 템플릿을 뿌려주는 것을 지원한다.  이 기능은
꽤 일반적이지 않기 때문에 플라스크에 직접적으로 노출되지 않지만, 아래처럼 여러분이
쉽게 직접 구현할 수 있다::

    from flask import Response

    def stream_template(template_name, **context):
        app.update_template_context(context)
        t = app.jinja_env.get_template(template_name)
        rv = t.stream(context)
        rv.enable_buffering(5)
        return rv

    @app.route('/my-large-page.html')
    def render_large_template():
        rows = iter_all_rows()
        return Response(stream_template('the_template.html', rows=rows))

여기서의 기법은 어플리케이션의 진자2 환경에서 템플릿 객체를 얻고 문자열 대신
스트림 객체를 반환하는 :meth:`~jinja2.Template.render` 대신 
:meth:`~jinja2.Template.stream` 를 호출하는 것이다.  플라스크 템플릿 렌더 함수를
지나치고 템플릿 객체 자체를 사용하고 있기 때문에 
:meth:`~flask.Flask.update_template_context` 를 호출하여 렌더 컨텍스트를 갱신하도록
보장해야한다.  그리고 나서 스트림을 순환하면서 템플릿을 해석한다. 매번 여러분은 yield
를 호출하기 때문에 서버는 클라이언트로 내용을 밀어내어 보낼 것이고 여러분은 
``rv.enable_buffering(size)`` 을 가지고 템플릿 안에 몇가지 항목을 버퍼링하기를 원할지도
모른다.  ``5`` 가 보통 기본값이다.

컨텍스트를 가진 스트리밍
------------------------

.. versionadded:: 0.9

여러분이 데이터를 스트리밍할 때, 요청 컨텍스트는 그 함수가 호출된 순간 이미
종료된다는 것에 주목해라.  플라스크 0.9 는 생성기가 수행하는 동안 요청 컨텍스트를
유지하게 해주는 조력자를 제공한다::

    from flask import stream_with_context, request, Response

    @app.route('/stream')
    def streamed_response():
        def generate():
            yield 'Hello '
            yield request.args['name']
            yield '!'
        return Response(stream_with_context(generate()))


:func:`~flask.stream_with_context` 함수 없다면 여러분은 그 시점에 :class:`RuntimeError`
를 얻을 것이다.
