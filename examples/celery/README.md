Background Tasks with Celery
============================

This example shows how to configure Celery with Flask, how to set up an API for
submitting tasks and polling results, and how to use that API with JavaScript. See
[Flask's documentation about Celery](https://flask.palletsprojects.com/patterns/celery/).

From this directory, create a virtualenv and install the application into it. Then run a
Celery worker.

```shell
$ python3 -m venv .venv
$ . ./.venv/bin/activate
$ pip install -r requirements.txt && pip install -e .
$ celery -A make_celery worker --loglevel INFO
```

In a separate terminal, activate the virtualenv and run the Flask development server.

```shell
$ . ./.venv/bin/activate
$ flask -A task_app run --debug
```

Go to http://localhost:5000/ and use the forms to submit tasks. You can see the polling
requests in the browser dev tools and the Flask logs. You can see the tasks submitting
and completing in the Celery logs.
