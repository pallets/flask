Background Tasks with Celery
============================

If your application has a long running task, such as processing some uploaded data or
sending email, you don't want to wait for it to finish during a request. Instead, use a
task queue to send the necessary data to another process that will run the task in the
background while the request returns immediately.

`Celery`_ is a powerful task queue that can be used for simple background tasks as well
as complex multi-stage programs and schedules. This guide will show you how to configure
Celery using Flask. Read Celery's `First Steps with Celery`_ guide to learn how to use
Celery itself.

.. _Celery: https://celery.readthedocs.io
.. _First Steps with Celery: https://celery.readthedocs.io/en/latest/getting-started/first-steps-with-celery.html

The Flask repository contains `an example <https://github.com/pallets/flask/tree/main/examples/celery>`_
based on the information on this page, which also shows how to use JavaScript to submit
tasks and poll for progress and results.


Install
-------

Install Celery from PyPI, for example using pip:

.. code-block:: text

    $ pip install celery


Integrate Celery with Flask
---------------------------

You can use Celery without any integration with Flask, but it's convenient to configure
it through Flask's config, and to let tasks access the Flask application.

Celery uses similar ideas to Flask, with a ``Celery`` app object that has configuration
and registers tasks. While creating a Flask app, use the following code to create and
configure a Celery app as well.

.. code-block:: python

    from celery import Celery, Task

    def celery_init_app(app: Flask) -> Celery:
        class FlaskTask(Task):
            def __call__(self, *args: object, **kwargs: object) -> object:
                with app.app_context():
                    return self.run(*args, **kwargs)

        celery_app = Celery(app.name, task_cls=FlaskTask)
        celery_app.config_from_object(app.config["CELERY"])
        celery_app.set_default()
        app.extensions["celery"] = celery_app
        return celery_app

This creates and returns a ``Celery`` app object. Celery `configuration`_ is taken from
the ``CELERY`` key in the Flask configuration. The Celery app is set as the default, so
that it is seen during each request. The ``Task`` subclass automatically runs task
functions with a Flask app context active, so that services like your database
connections are available.

.. _configuration: https://celery.readthedocs.io/en/stable/userguide/configuration.html

Here's a basic ``example.py`` that configures Celery to use Redis for communication. We
enable a result backend, but ignore results by default. This allows us to store results
only for tasks where we care about the result.

.. code-block:: python

    from flask import Flask

    app = Flask(__name__)
    app.config.from_mapping(
        CELERY=dict(
            broker_url="redis://localhost",
            result_backend="redis://localhost",
            task_ignore_result=True,
        ),
    )
    celery_app = celery_init_app(app)

Point the ``celery worker`` command at this and it will find the ``celery_app`` object.

.. code-block:: text

    $ celery -A example worker --loglevel INFO

You can also run the ``celery beat`` command to run tasks on a schedule. See Celery's
docs for more information about defining schedules.

.. code-block:: text

    $ celery -A example beat --loglevel INFO


Application Factory
-------------------

When using the Flask application factory pattern, call the ``celery_init_app`` function
inside the factory. It sets ``app.extensions["celery"]`` to the Celery app object, which
can be used to get the Celery app from the Flask app returned by the factory.

.. code-block:: python

    def create_app() -> Flask:
        app = Flask(__name__)
        app.config.from_mapping(
            CELERY=dict(
                broker_url="redis://localhost",
                result_backend="redis://localhost",
                task_ignore_result=True,
            ),
        )
        app.config.from_prefixed_env()
        celery_init_app(app)
        return app

To use ``celery`` commands, Celery needs an app object, but that's no longer directly
available. Create a ``make_celery.py`` file that calls the Flask app factory and gets
the Celery app from the returned Flask app.

.. code-block:: python

    from example import create_app

    flask_app = create_app()
    celery_app = flask_app.extensions["celery"]

Point the ``celery`` command to this file.

.. code-block:: text

    $ celery -A make_celery worker --loglevel INFO
    $ celery -A make_celery beat --loglevel INFO


Defining Tasks
--------------

Using ``@celery_app.task`` to decorate task functions requires access to the
``celery_app`` object, which won't be available when using the factory pattern. It also
means that the decorated tasks are tied to the specific Flask and Celery app instances,
which could be an issue during testing if you change configuration for a test.

Instead, use Celery's ``@shared_task`` decorator. This creates task objects that will
access whatever the "current app" is, which is a similar concept to Flask's blueprints
and app context. This is why we called ``celery_app.set_default()`` above.

Here's an example task that adds two numbers together and returns the result.

.. code-block:: python

    from celery import shared_task

    @shared_task(ignore_result=False)
    def add_together(a: int, b: int) -> int:
        return a + b

Earlier, we configured Celery to ignore task results by default. Since we want to know
the return value of this task, we set ``ignore_result=False``. On the other hand, a task
that didn't need a result, such as sending an email, wouldn't set this.


Calling Tasks
-------------

The decorated function becomes a task object with methods to call it in the background.
The simplest way is to use the ``delay(*args, **kwargs)`` method. See Celery's docs for
more methods.

A Celery worker must be running to run the task. Starting a worker is shown in the
previous sections.

.. code-block:: python

    from flask import request

    @app.post("/add")
    def start_add() -> dict[str, object]:
        a = request.form.get("a", type=int)
        b = request.form.get("b", type=int)
        result = add_together.delay(a, b)
        return {"result_id": result.id}

The route doesn't get the task's result immediately. That would defeat the purpose by
blocking the response. Instead, we return the running task's result id, which we can use
later to get the result.


Getting Results
---------------

To fetch the result of the task we started above, we'll add another route that takes the
result id we returned before. We return whether the task is finished (ready), whether it
finished successfully, and what the return value (or error) was if it is finished.

.. code-block:: python

    from celery.result import AsyncResult

    @app.get("/result/<id>")
    def task_result(id: str) -> dict[str, object]:
        result = AsyncResult(id)
        return {
            "ready": result.ready(),
            "successful": result.successful(),
            "value": result.result if result.ready() else None,
        }

Now you can start the task using the first route, then poll for the result using the
second route. This keeps the Flask request workers from being blocked waiting for tasks
to finish.

The Flask repository contains `an example <https://github.com/pallets/flask/tree/main/examples/celery>`_
using JavaScript to submit tasks and poll for progress and results.


Passing Data to Tasks
---------------------

The "add" task above took two integers as arguments. To pass arguments to tasks, Celery
has to serialize them to a format that it can pass to other processes. Therefore,
passing complex objects is not recommended. For example, it would be impossible to pass
a SQLAlchemy model object, since that object is probably not serializable and is tied to
the session that queried it.

Pass the minimal amount of data necessary to fetch or recreate any complex data within
the task. Consider a task that will run when the logged in user asks for an archive of
their data. The Flask request knows the logged in user, and has the user object queried
from the database. It got that by querying the database for a given id, so the task can
do the same thing. Pass the user's id rather than the user object.

.. code-block:: python

    @shared_task
    def generate_user_archive(user_id: str) -> None:
        user = db.session.get(User, user_id)
        ...

    generate_user_archive.delay(current_user.id)
