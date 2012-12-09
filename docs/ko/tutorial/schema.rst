.. _tutorial-schema:

스텝 1: 데이터베이스 스키마
=======================

먼저 우리는 데이터베이스 스키마를 생성해야 한다. 우리의 어플리케이션을 위해서는
단지 하나의 테이블만 필요하며 사용이 매우 쉬운 SQLite를 지원하기를 원한다.
다음의 내용을 `schema.sql` 이라는 이름의 파일로 방금 생성한 `flaskr` 폴더에 저장한다.


.. sourcecode:: sql

    drop table if exists entries;
    create table entries (
      id integer primary key autoincrement,
      title string not null,
      text string not null
    );

이 스키마는 `entries` 라는 이름의 테이블로 구성되어 있으며 이 테이블의 
각 row에는 `id`, `title`, `text` 컬럼으로 구성된다. `id` 는 자동으로 증가되는
정수이며 프라이머리 키(primary key) 이다. 나머지 두개의 컬럼은 null이 아닌 
문자열(strings) 값을 가져야 한다.
    

계속해서 Step 2: 어플리케이션 셋업 코드를 보자.  :ref:`tutorial-setup`.
