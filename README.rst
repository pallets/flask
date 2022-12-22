Flask (не фляга)
=====

Flask - это облегченный фреймворк веб-приложений `WSGI`_. Он разработан
для того, чтобы сделать начало работы быстрым и легким, с возможностью масштабирования до
сложных приложений. Он начинался как простая оболочка вокруг `Werkzeug`_
и `Jinja`_ и стал одним из самых популярных
фреймворков веб-приложений на Python.

Flask предлагает предложения, но не применяет никаких зависимостей или
макета проекта. Разработчик сам выбирает инструменты и
библиотеки, которые он хочет использовать. Сообщество предоставляет множество расширений
, которые упрощают добавление новых функций.

.. _WSGI: https://wsgi.readthedocs.io/
.. _Werkzeug: https://werkzeug.palletsprojects.com/
.. _Jinja: https://jinja.palletsprojects.com/


Установочка))
----------

Install and update using `pip`_:

.. code-block:: text

    $ pip install -U Flask

.. _pip: https://pip.pypa.io/en/stable/getting-started/

Простой пример)))):
----------------

.. code-block:: python

    # save this as app.py
    from flask import Flask

    app = Flask(__name__)

    @app.route("/")
    def hello():
        return "Hello, World!"

.. code-block:: text

    $ flask run
      * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)


Сопутствие
------------

Рекомендации по настройке среды разработки и тому, как внести
свой вклад в Flask, см. в разделе "Рекомендации по внесению вклада`_.

.. _Способствующие руководящие принципы: https://github.com/pallets/flask/blob/main/CONTRIBUTING.rst


Для донатеров
------

Организация Pallets разрабатывает и поддерживает Flask и библиотеки
, которые она использует. Чтобы расширить сообщество участников и пользователей и
позволить сопровождающим уделять больше времени проектам, "пожалуйста
, сделайте пожертвование сегодня`_.

.. _Пожалуйста задонатьте сегодня :>  : https://palletsprojects.com/donate


Полезные ссылочки
-----

-   Документация: https://flask.palletsprojects.com/
-   Изменения: https://flask.palletsprojects.com/changes/
-   PyPI Releases: https://pypi.org/project/Flask/
-   Исходный код: https://github.com/pallets/flask/
-   Отслеживание проблем: https://github.com/pallets/flask/issues/
-   Вебсайт: https://palletsprojects.com/p/flask/
-   Твитер: https://twitter.com/PalletsTeam
-   Чат: https://discord.gg/pallets
