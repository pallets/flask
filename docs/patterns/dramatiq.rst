Dramatiq Background Tasks
=========================

Often when processing web requests there are things that can be moved
out of the request-response cylce in order to conserve time.  An
example of such a workload is sending an e-mail: not only can it take
a while, but it can fail so it makes sense to move that sort of
operation to a background queue where it can be processed
asynchronously and retried if necessary.

Dramatiq_ is a powerful distributed task processing library for
Python 3.  This guide will show you how to use Dramatiq and Flask
together.  We assume you've already read the Dramatiq `user guide`_.


Installation
------------

Dramatiq is a separate Python package and it comes in two flavors::

    $ pip install dramatiq[rabbitmq,watch]

installs it with support for RabbitMQ as a task broker, and::

    $ pip install dramatiq[redis,watch]

installs it with support for Redis as a task broker.


Configuration
-------------

There's nothing Flask-specific to set up, but you do need to tell
Dramatiq what broker it should use.  For this example we're going to
use RabbitMQ, so create an instance of ``RabbitmqBroker`` in a module
called ``tasks.py`` and then set it as the default broker::

    import dramatiq
    import os

    from dramatiq.brokers.rabbitmq import RabbitmqBroker

    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://127.0.0.1:5672")
    broker = RabbitmqBroker(url=rabbitmq_url)
    dramatiq.set_broker(broker)

After that's done you can start writing actors.  In that same module::

    @dramatiq.actor
    def add(x, y):
        print(f"The sum of {x} and {y} is {x + y}.")

You can send that actor a message from your view by calling its
``send`` method::

    from . import tasks

    @app.route("/", methods=["POST"])
    def compute_sum():
        tasks.add.send(request.form["x"], request.form["y"])
        return "Deferred", 202


Running workers
---------------

Since Dramatiq actors process message asynchronously, you'll have to
run a separate set of processes -- called workers -- to actually
process all the messages in the queue.  To do that, just invoke the
``dramatiq`` command pointing it to where your tasks are defined::

    $ env PYTHONPATH=. dramatiq tasks


Next steps
----------

Check out `this repo`_ for an app that uses Dramatiq with Flask.


.. _Dramatiq: https://dramatiq.io
.. _user guide: https://dramatiq.io/guide.html
.. _this repo: https://github.com/Bogdanp/flask_dramatiq_example
