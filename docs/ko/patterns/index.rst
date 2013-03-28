.. _patterns:

플라스크를 위한 패턴들
======================

어떤 것들은 충분히 일반적이어서 여러분이 대부분의 웹 어플리케이션에서 찾을 가능성이 높다. 예를 들면 많은 어플리케이션들이 관계형 데이타베이스와 사용자 인증을 사용한다. 그 경우에, 그 어플리케이션들은 요청 초반에 데이타베이스 연결을 열고 사용자 테이블에서 현재 로그인된 사용자의 정보를 얻을 것이다. 요청의 마지막에는 그 데이타베이스 연결을 다시 닫는다. 

`플라스크 스니핏 묶음(Flask Snippet Archives) <http://flask.pocoo.org/snippets/>`_ 에 많은 사용자들이 기여한 스니핏과 패턴들이 있다.

.. toctree::
   :maxdepth: 2

   packages
   appfactories
   appdispatch
   urlprocessors
   distribute
   fabric
   sqlite3
   sqlalchemy
   fileuploads
   caching
   viewdecorators
   wtforms
   templateinheritance
   flashing
   jquery
   errorpages
   lazyloading
   mongokit
   favicon
   streaming
   deferredcallbacks
   methodoverrides
   requestchecksum
