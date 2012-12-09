.. _tutorial-folders:

스텝 0: 폴더를 생성하기
============================

어플리케이션 개발을 시작하기전에, 어플리케이션에서 사용할 폴더를 만들자 ::

    /flaskr
        /static
        /templates


`flaskr` 폴더는 Python 패키지가 아니다. 단지 우리의 파일들을 저장할 장소이다.
우리는 이 폴더 안에 데이터베이스 스키마 뿐만 아니라 다른 앞으로 소개될 다른
스텝에 나오는 주요 모듈들 넣을 곳이다. `static` 폴더 내 파일들은 `HTTP` 를 
통해 어플리케이션 사용자들이 이용할 수 있다. 이 폴더는 css와 javascript 
파일들이 저장되는 곳이다. Flasks는 `templates` 폴더에서 `Jinja2`_ 템플릿을 찾을 것이다



계속해서 Step 1:데이타베이스 스키마를 보자 :ref:`tutorial-schema`.

.. _Jinja2: http://jinja.pocoo.org/2/
