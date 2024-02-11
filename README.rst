Flask
=====

Flask is a lightweight `WSGI`_ web application framework. It is designed
to make getting started quick and easy, with the ability to scale up to
complex applications. It began as a simple wrapper around `Werkzeug`_
and `Jinja`_ and has become one of the most popular Python web
application frameworks.

Flask offers suggestions, but doesn't enforce any dependencies or
project layout. It is up to the developer to choose the tools and
libraries they want to use. There are many extensions provided by the
community that make adding new functionality easy.

.. _WSGI: https://wsgi.readthedocs.io/
.. _Werkzeug: https://werkzeug.palletsprojects.com/
.. _Jinja: https://jinja.palletsprojects.com/

Flask supports Python 3.8 and newer, but we recommend using the latest version.

Installing
----------

Install and update using `pip`_:

.. code-block:: text

    $ pip install -U Flask

.. _pip: https://pip.pypa.io/en/stable/getting-started/


Overview
------------

Flask can be as simple as a single python file with the following pieces:

#. Importing Flask
#. Configuring the router
#. Defining a method of returning code, typically HTML. 

.. code-block:: python

    # save this as app.py
    from flask import Flask

    app = Flask(__name__)

    @app.route("/")
    def hello():
        return "Hello, World!"

This python can be compiled and ran using flash run:

.. code-block:: text

    $ flask run
      * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)

However, as the project grows, it is recommended to structure your app with packages. An example can be found in our docs: https://flask.palletsprojects.com/en/3.0.x/tutorial/layout/



Why Flask?
----------

If you're wondering why use Flask, here are a few benefits it provides:

**Simplicity:** Flask is designed to be simple and easy to use, making it ideal for beginners and experienced developers alike. Its minimalist approach allows developers to focus on building their application logic without getting bogged down by unnecessary complexity.

**Flexibility:** Flask is highly flexible and can be easily customized to fit the specific requirements of your project. You can use only the components you need and integrate third-party extensions as necessary, giving you full control over your application's architecture.

**Lightweight:** As a microframework, Flask has minimal dependencies and a small footprint, making it lightweight and efficient. This results in faster performance and reduced overhead compared to larger frameworks.

**Scalability:** Flask's lightweight and modular architecture make it well-suited for building scalable web applications. You can start small and add features as your application grows, ensuring that it remains efficient and manageable over time.

**Extensibility:** Flask has a rich ecosystem of extensions that provide additional functionality for common tasks such as authentication, database integration, and form validation. These extensions can save you time and effort by providing pre-built solutions for common challenges.

**Community and Documentation:** Flask has a large and active community of developers who contribute to its development and provide support to other users. The official Flask documentation is comprehensive and well-maintained, making it easy to get started and find answers to your questions.

Use-cases:
----------

With Flask, you can unleash your creativity to build a variety of cool projects. From developing web applications ranging from simple blogs to complex e-commerce platforms, to creating RESTful APIs for mobile apps and IoT devices, Flask offers flexibility and simplicity. You can also dive into real-time web applications like chat apps, craft interactive data visualizations, deploy machine learning models, build microservices architectures, develop interfaces for IoT devices, and even explore blockchain applications. With its lightweight architecture and extensive ecosystem, Flask empowers you to bring your ideas to life with ease and efficiency.


Contributing
------------

For guidance on setting up a development environment and how to make a
contribution to Flask, see the `contributing guidelines`_.

.. _contributing guidelines: https://github.com/pallets/flask/blob/main/CONTRIBUTING.rst


Donate
------

The Pallets organization develops and supports Flask and the libraries
it uses. In order to grow the community of contributors and users, and
allow the maintainers to devote more time to the projects, `please
donate today`_.

.. _please donate today: https://palletsprojects.com/donate


Links
-----

-   Documentation: https://flask.palletsprojects.com/
-   Changes: https://flask.palletsprojects.com/changes/
-   PyPI Releases: https://pypi.org/project/Flask/
-   Source Code: https://github.com/pallets/flask/
-   Issue Tracker: https://github.com/pallets/flask/issues/
-   Chat: https://discord.gg/pallets
