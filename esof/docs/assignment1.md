![FEUP image](https://sigarra.up.pt/feup/pt/WEB_GESSI_DOCS.download_file?p_name=F-370784536/logo_cores_oficiais.jpg)
#**Software Processes and Project Management**

##**Integrated Masters in Informatics and Computer Engineering**

![flask image](http://flask.pocoo.org/static/logo/flask.png)

###**Brief description of Flask**

[*Flask*](http://flask.pocoo.org/) is a micro Python web framework created by Armin Ronacher and based on Werkzeug toolkit  and Jinja2 template engine. Launched in 2010, this framework has the flexibility of Python which enables a simple model for web development.
Flask is called a micro framework because it keeps the core simple but extensible. By default, Flask does not include a database abstraction layer, form validation or anything else where different libraries  already exist that can handle that. Instead, Flask supports extensions to add such functionality to an application as if it was implemented in Flask itself, giving the user the freedom to customize the web framework. Several extensions provide database integration, form validation, uploading handling or various open authentication technologies.
Some other Flask features are development server and debugger, integrated support for unit testing, support for secure cookies and a very extensive documentation, allowing newcomers to quickly familiarize with the framework <sup>1</sup>.

Applications that use the Flask framework include [*Pinterest*](https://pt.pinterest.com/), [*LinkedIn*](https://www.linkedin.com/), and the community web page for [*Flask*](http://flask.pocoo.org/) itself. The latest stable version of Flask is 0.11 launched in June 2016. As of mid 2016, despite of the lack of a major release, Flask was the most popular Python web development framework on [*GitHub*](https://github.com/) <sup>2</sup>.

Flask is a project available under [BSD license](http://flask.pocoo.org/docs/0.11/license/#flask-license) <sup>1</sup>.


###**Development Process**


####**Software Development**

In an open-source project becomes hard to implement a traditional software development process, considering the lack of a true management of the project. Nevertheless,  it's still possible to see some traces of it.
The project in the early stages followed a **Software Prototyping** design to develop some concepts behind Flask and also to try out some design options. The developed prototype was then presented to the community as an April’s Fool joke, to evaluate the acceptance of the community. As this showed to be a great success, and with the growing community attention on Flask, more several early functional prototypes were released to get more precise requirements of the project <sup>3,4</sup>.

Recently, the design transitioned to **Incremental Development and Delivery** aiming to build a final product over the early prototypes through the incremental adding of requested features and correction of bugs. This can be particularly seen by the number of functional releases of the project since the first version <sup>4</sup>.

####**Contributions**

To contribute to the project is necessary to create a fork and make the changes to the code there. When the modifications are implemented, becomes necessary to make a *pull request* and so the original owner of the repository can accept or reject he changes. The project also have a [section](https://github.com/pallets/flask/issues) were you can find some known issues and feature requests, usually both of them are well described and have a specific discussion area.

####**Repository structure**

The repository is divided in several branches and the main categories are:
-   maintenance;
-   feature;
-   master.

This organization allows :
-   simultaneous working in different areas;
-   support to applications that uses a old version of this framework.

This structure design is been kept organised by the founder of the project.  

###**Opinions, Critics and Alternatives**

####**Project activity**

Currently, Flask is considered almost complete in terms of major features. Nevertheless, the project is still full of activity with near 400 contributors and with currently around 100 open issues. Actually, some of these issues are tagged as beginner friendly, which encourages the newest people in programming to contribute to the project.

####**Project Structure**

Since this project is open-source, it is build by a big community and as so it is not easy to keep a well defined structure (related to the incremental development process). Despite this, the project is well documented, which makes it easier to newcomers to integrate the project.

####**Project Development**

We believe that the methods **Software Prototype** and **Incremental Development** and Delivery are the ones that best fits Flask. It's very hard to keep a good structure on code when the project is open source and this processes help. Also, these processes allow the developers to go back to a previous phase, something not possible in other processes like Waterfall. Returning to a previous phase, sometimes, can occur because on the beginning of the project the requirements are rarely gathered. Instead of that, they are based on early releases (“Release early, release often, and listen to your customers” <sup>5</sup>),  creating a tight feedback loop between developers and testers or users. Also, since this project is developed by several people, with minimum communication between them, it can lead to the lack of code reuse, increasing the chances of finding repeated code<sup>4</sup>.

###**Group Contribution**

|Name|Contribution|
| :---: | :---: |
|José Oliveira|25%|
|Manuel Gomes|25%|
|Marcelo Ferreira|25%|
|Pedro Dias|25%|

###**Group Members**

|Name|Number|
| :---: | :---: |
|José Oliveira|up201406208|
|Manuel Gomes|up201402679 |
|Marcelo Ferreira|up201405323|
|Pedro Dias|up201404178|

###**References**

<sup>1</sup>  Armin Ronacher, Flask, <http://flask.pocoo.org/> , 06 October 2016

<sup>2</sup>  Python Software Foundation, Package List - Flask <https://pypi.python.org/pypi/Flask/0.11.1>, 7 October 2016

<sup>3</sup>  Armin Ronacher, Opening the Flask, <http://mitsuhiko.pocoo.org/flask-pycon-2011.pdf>. 7 October 2016

<sup>4</sup>  Whiten, Jeffrey L; Lonnie D. Bentley, Selecting a Development Approach, System Analysis and Design Methods 6th Edition, 2003
Whitten, Jeffrey L.; Lonnie D. Bentley, Kevin C. Dittman.

<sup>5</sup> Raymond, Eric (1997-05-27). Release Early, Release Often. The Cathedral and the Bazaar: Musings on Linux and Open Source by an Accidental Revolutionary. 

###**External links**

[Official website](http://flask.pocoo.org/)

[Flask](https://github.com/pallets/flask) on [GitHub](https://github.com/)
