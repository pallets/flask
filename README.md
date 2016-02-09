
![Flask logo](http://flask.pocoo.org/static/logo/flask.svg)



###What to use Flask for and when to use it.
Flask is an all-purpose *microframework* for Python based on Werkzeug and Jinja2. It is ideally suited for Python developers looking for an easily extensible framework to quickly create smaller apps. However, with some effort it can also accomodate the requirements of [larger projects](https://github.com/mitsuhiko/flask/wiki/Large-app-how-to). Flask has great unofficial and official documentation and an active development community. 

######Unique aspects 

Flask has several unique aspects which sets it apart from more tightly integrated frameworks. 

For instance, Flask does not force developers to use particular tools or libraries, nor does it have built-in components where third-party libraries provide common functions. Instead, Flask is easily extensible to add extra functionality. If a desired extension [doesn't exist](http://flask.pocoo.org/extensions/), developers can write a stand-alone library and bridge that library to Flask by wrapping it in an extension.  
 
Flask developers have the flexibility to choose how they want their data to be stored and manipulated. For instance, for projects that aren't suited to work with a standard ORM, Flask applications can use existing Python libaries like SQLAlchemy, Django ORM, Peewee, PonyORM or SQLObject. This makes Flask easier to use with non-relational databases than more tightly integrated frameworks.

Unlike frameworks which use the *module approach*, Flask utilizes *application dispatching* which isolates the same or different Flask applications from each other in the same Python interpreter process. This is useful for developers who want to use multiple instances of the same application with different configurations, OR ? 

<br>

###FAQs:
#####Is it ready?

It's still not 1.0 but it's shaping up nicely and is already widely used. We believe that the project doesn't have to fundamentally change to remain relevant. Therefore, the future of Flask is that it becomes more stable and sees minimal changes beyond the required new releases and updates. Slight improvements will also be made to the API over time but there aren't plans to break it.
 
#####What do I need to get started?

 All dependencies are installed by using `pip install Flask`. We encourage you to use [Virtualenv](https://virtualenv.pypa.io/en/latest/). Check the [docs](flask.pocoo.org/docs/installation/) for complete installation and usage instructions. Also read the [Quickstart Guide](flask.pocoo.org/docs/quickstart/)

#####Where are the docs?

Go to [http://flask.pocoo.org/docs/](http://flask.pocoo.org/docs/) for a prebuilt version of the current documentation. Otherwise build them yourself from the sphinx sources in the docs folder.

#####Where are the tests?

Good that you're asking.  The tests are in the [`tests/`](https://github.com/mitsuhiko/flask/tree/master/tests) folder.  To run the tests use the `py.test` testing tool: `$ py.test`

#####Where can I get help?
- The #pocoo IRC channel on irc.freenode.net
-  Ask on the [mailinglist](http://flask.pocoo.org/mailinglist/)
- [The flask community page ](http://flask.pocoo.org/community/)


#####What’s in the Box?
- Built in development server and debugger
- Integrated unit testing support
- RESTful request dispatching
- Uses Jinja2 templating
- Security:
  - Session based authentication
  - Role management
  - Password encryption
  - Basic HTTP authentication
  - Token based authentication
  - Token based account activation (optional)
  - Token based password recovery / resetting (optional)
  - User registration (optional)
  - Login tracking (optional)
  - JSON/Ajax Support
  - Support for secure cookies (client side sessions)
- 100% WSGI 1.0 compliant
- Unicode based
- Extensively documented
