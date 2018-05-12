Flask
=====

플라스크는 가벼운 WSGI_ 웹 어플리케이션 프레임워크입니다. 이것은 복잡한 어플리케이션으로의 확장을 쉽고 빠르게 시작할 수 있도록 디자인 되어 있습니다. 이것은 Werkzeug_ 와 Jinja_ 를 래핑하는 것으로 시작되었으나 현재는 가장 인기있는 파이썬 어플리케이션 프레임 워크 중 하나가 되었습니다.

Flask는 종속된 것이나 프로젝트 레이아웃을 강제하지 않고 제안만 합니다.  이것은 개발자에게 자신이 원하는 툴을 선택할 수 있도록 합니다. 새로운 기능을 쉽게 추가할 수 있도록 커뮤니티에서 제공하는 확장 기능이 많이 있습니다.


설치하기
----------

pip_를 이용하여 설치 및 업데이트를 합니다.

.. code-block:: text

    pip install -U Flask


간단한 예시
----------------

.. code-block:: python

    from flask import Flask

    app = Flask(__name__)

    @app.route('/')
    def hello():
        return 'Hello, World!'

.. code-block:: text

    $ FLASK_APP=hello.py flask run
     * Serving Flask app "hello"
     * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)


Donate
------


Pallets 조직에서는 Flask의 사용법을 정리함으로써 발전시키고 지지하고 있습니다.
사용자와 기여자의 커뮤니티를 키우고, 관리자들이 더 많은 시간을 프로젝트에 할애할 수 있도록, `오늘 기부를 부탁드립니다`_.


.. _오늘 기부를 부탁드립니다: https://psfmember.org/civicrm/contribute/transact?reset=1&id=20


Links
-----

* Website: https://www.palletsprojects.com/p/flask/
* Documentation: http://flask.pocoo.org/docs/
* License: `BSD <https://github.com/pallets/flask/blob/master/LICENSE>`_
* Releases: https://pypi.org/project/Flask/
* Code: https://github.com/pallets/flask
* Issue tracker: https://github.com/pallets/flask/issues
* Test status:

  * Linux, Mac: https://travis-ci.org/pallets/flask
  * Windows: https://ci.appveyor.com/project/pallets/flask

* Test coverage: https://codecov.io/gh/pallets/flask

.. _WSGI: https://wsgi.readthedocs.io
.. _Werkzeug: https://www.palletsprojects.com/p/werkzeug/
.. _Jinja: https://www.palletsprojects.com/p/jinja/
.. _pip: https://pip.pypa.io/en/stable/quickstart/
