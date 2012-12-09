.. _tutorial-dbinit:

스텝 3: 데이터베이스 생성하기 
=============================

Flaskr은 이전에 설명한 대로 데이터베이스를 사용하는 어플리케이션이고 
좀더 정확하게는 관계형 데이터베이스 시스템에 의해 구동되는 어플리케이션이다.
이러한 시스템은 어떻게 데이터를 저장할지에 대한 정보를 가지고 있는 스키마가 필요하다.
그래서 처음으로 서버를 실행하기 전에 스키마를 생성하는 것이 중요하다.

이러한 스키마는 `schema.sql` 파일을 이용하여 `sqlite3` 명령어를 사용하여
다음과 같이 만들 수 있다.::

    sqlite3 /tmp/flaskr.db < schema.sql

이방법에서의 단점은 sqlite3 명령어가 필요하다는 점인데, sqlite3 명령어는 모든
시스템들에서 필수적으로 설치되어 있는 것은 아니기 때문이다.  
한가지 추가적인 문제는 데이터베이스 경로로 제공받은 어떤 경로들은 오류를 발생시킬 수도 있다는 것이다.
당신의 어플리케이션에 데이터베이스를 초기화 하는 함수를 추가하는 것은 좋은 생각이다.

만약 당신이 데이터베이스를 초기화 하는 함수를 추가하기 원한다면
먼저 contextlib 패키지에 있는 :func:`contextlib.closing` 함수를 import 해야한다.
만약 Python 2.5를 사용하고 싶다면 먼저 `with` 구문을 추가적으로 사용해야 하다.
(`__future__` 를 반드시 제일 먼저 import 해야 한다.). 
따라서, 다음의 라인들을 기존의 `flaskr.py` 파일에 추가한다. ::

    from __future__ import with_statement
    from contextlib import closing

다음으로 우리는 데이터베이스를 초기화 시키는 `init_db` 함수를 만들 수 있다. 
이 함수에서 우리는 앞서 정의한 `connect_db` 함수를 사용할 수 있다.
`flaskr.py` 파일의 `connect_db` 함수 아래에 다음의 내용을 추가 하자.::

    def init_db():
        with closing(connect_db()) as db:
            with app.open_resource('schema.sql') as f:
                db.cursor().executescript(f.read())
            db.commit()


:func:`~contextlib.closing` 함수는 `with` 블럭안에서 연결한 커넥션을 유지하도록
도와준다. :func:`~flask.Flask.open_resource` 는 어플리케이션 객체의 함수이며 
영역 밖에서도 기능을 지원하며 `with` 블럭에서 직접적으로 사용할 수 있다.
이 함수를 통해서 리소스 경로(`flaskr` 의 폴더)의 파일을 열고 그 값을 읽을 수 있다.
우리는 이것을 이용하여 데이터베이스에 연결하는 스크립트를 실행시킬 것이다.

우리가 데이터베이스에 연결할 때 우리는 커서를 제공하는 커넥션 객체를 얻는다. 
(여기에서는 `db` 라고 부르려고 한다.) 커서에는 전체 스크립트를 실행하는 메소드를 가지고 있다.
마지막으로, 우리는 변경사항들을 커밋해야 한다. SQLite 3 이다 다른 트랜잭션 데이터베이스들은
명시적으로 커밋을 하도록 선언하지 않는 이상 진행하지 않는다.

이제 Python 쉘에서 다음 함수를 import 하여 실행시키면 데이터베이스 생성이 가능하다.::

>>> from flaskr import init_db
>>> init_db()

.. admonition:: Troubleshooting

   만약 테이블을 찾을 수 없다는 예외사항이 발생하면 `init_db` 함수를 
   호출하였는지 확인하고 테이블 이름이 정확한지 확인하라.
   (예를들면 단수형, 복수형과 같은 실수..)

다음 섹션에서 계속된다.  :ref:`tutorial-dbcon`
