JavaScript Ajax Example
=======================

Demonstrates how to post form data and process a JSON response using
JavaScript. This allows making requests without navigating away from the
page. Demonstrates using |fetch|_, |XMLHttpRequest|_,  and
|jQuery.ajax|_. See the `Flask docs`_ about JavaScript and Ajax.

.. |fetch| replace:: ``fetch``
.. _fetch: https://developer.mozilla.org/en-US/docs/Web/API/WindowOrWorkerGlobalScope/fetch

.. |XMLHttpRequest| replace:: ``XMLHttpRequest``
.. _XMLHttpRequest: https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest

.. |jQuery.ajax| replace:: ``jQuery.ajax``
.. _jQuery.ajax: https://api.jquery.com/jQuery.ajax/

.. _Flask docs: https://flask.palletsprojects.com/patterns/jquery/


Install
-------

.. code-block:: text

    $ python3 -m venv venv
    $ . venv/bin/activate
    $ pip install -e .


Run
---

.. code-block:: text

    $ flask --app js_example run

Open http://127.0.0.1:5000 in a browser.


Test
----

.. code-block:: text

    $ pip install -e '.[test]'
    $ coverage run -m pytest
    $ coverage report
