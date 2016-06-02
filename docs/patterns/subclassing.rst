Subclassing Flask
=================

The :class:`~flask.Flask` class is designed for subclassing.

One reason to subclass would be customizing the Jinja2 :class:`~jinja2.Environment`. For example, to add a new global template variable::

    from flask import Flask
    from datetime import datetime

    class MyFlask(Flask):
        """ Flask with more global template vars """

        def create_jinja_environment(self):
            """ Initialize my custom Jinja environment. """
            jinja_env = super(MyFlask, self).create_jinja_environment(self)
            jinja_env.globals.update(
                current_time = datetime.datetime.now()
            )
            return jinja_env

This is the recommended approach for overriding or augmenting Flask's internal functionality.
