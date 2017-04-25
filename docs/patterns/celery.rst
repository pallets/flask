Celery Based Background Tasks
=============================

Celery is a task queue for Python with batteries included.  It used to
have a Flask integration but it became unnecessary after some
restructuring of the internals of Celery with Version 3.  This guide fills
in the blanks in how to properly use Celery with Flask but assumes that
you generally already read the `First Steps with Celery
<http://docs.celeryproject.org/en/latest/getting-started/first-steps-with-celery.html>`_
guide in the official Celery documentation.

Installing Celery
-----------------

Celery is on the Python Package Index (PyPI), so it can be installed with
standard Python tools like :command:`pip` or :command:`easy_install`::

    $ pip install celery

Configuring Celery
------------------

The first thing you need is a Celery instance, this is called the celery
application.  It serves the same purpose as the :class:`~flask.Flask`
object in Flask, just for Celery.  Since this instance is used as the
entry-point for everything you want to do in Celery, like creating tasks
and managing workers, it must be possible for other modules to import it.

For instance you can place this in a ``tasks`` module.  While you can use
Celery without any reconfiguration with Flask, it becomes a bit nicer by
subclassing tasks and adding support for Flask's application contexts and
hooking it up with the Flask configuration.

This is all that is necessary to properly integrate Celery with Flask::

    from celery import Celery

    def make_celery(app):
        celery = Celery(app.import_name, backend=app.config['CELERY_RESULT_BACKEND'],
                        broker=app.config['CELERY_BROKER_URL'])
        celery.conf.update(app.config)
        TaskBase = celery.Task
        class ContextTask(TaskBase):
            abstract = True
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return TaskBase.__call__(self, *args, **kwargs)
        celery.Task = ContextTask
        return celery

The function creates a new Celery object, configures it with the broker
from the application config, updates the rest of the Celery config from
the Flask config and then creates a subclass of the task that wraps the
task execution in an application context.

Minimal Example
---------------

With what we have above this is the minimal example of using Celery with
Flask::

    from flask import Flask

    flask_app = Flask(__name__)
    flask_app.config.update(
        CELERY_BROKER_URL='redis://localhost:6379',
        CELERY_RESULT_BACKEND='redis://localhost:6379'
    )
    celery = make_celery(flask_app)


    @celery.task()
    def add_together(a, b):
        return a + b

This task can now be called in the background:

>>> result = add_together.delay(23, 42)
>>> result.wait()
65

Running the Celery Worker
-------------------------

Now if you jumped in and already executed the above code you will be
disappointed to learn that your ``.wait()`` will never actually return.
That's because you also need to run celery.  You can do that by running
celery as a worker::

    $ celery -A your_application.celery worker

The ``your_application`` string has to point to your application's package
or module that creates the `celery` object.
