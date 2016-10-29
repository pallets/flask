![FEUP image](https://sigarra.up.pt/feup/pt/WEB_GESSI_DOCS.download_file?p_name=F-370784536/logo_cores_oficiais.jpg)
#**Requirements Elicitation**

##**Integrated Masters in Informatics and Computer Engineering**

![flask image](http://flask.pocoo.org/static/logo/flask.png)

<a name="index"/>
##**Index**
1. [Requirements elicitation](#elicitation)
  1. [Introduction](#introduction)
  2. [Purpose](#purpose)
  3. [Scope](#scope)
  4. [Descripion](#description)
2. [Specific Requirements and Features](#specific)
3. [Use Cases](#usecases)
4. [Domain Model](#domainmodel)
5. [Group Contribution](#contribution)

<a name="elicitation"/>
##**Requirements Elicitation**
<a name="introduction"/>
###Introduction

  // TODO - FALAR

The development of Flask is made in a really simple and opened way. The big community that exists around Flask (???????) and the core of developers are the main responsible by the resolution of the issues and the implementation of the defined requirements as well as propose and introduce new ones.

  Requirements elicitation and analysis involves first collecting as many potentional requirements as possible, then refining them to form a complete, concise and consistent set of high-quality functional and non-functional requirements, and then analyzing them to start a preliminary model of the system to be developed. Functional requirementsare often modeled with the aid of use cases


Requirements elicitaiton and analysis involves first collecting as many potential requirements as possible, then refining them to form a complete, concise and consistent set of high-quality functional and non-functional requirements, and then analyzing them to start forming a preliminary model of the system to be developed. Functional requirements are often modeled wih the aid of use-cases and scenarios, while the analysis step starts to identify some of the candidate objects / classes that will be needed in the system.



//TODO How those the proposal of a new requirement works?


<a name="purpose"/>
###Purpose
  The purpose of this document is to provide a quick overview of the funcionality of Flask in particular for developers and stackholders. The document will particulary detail the requirements elicitation and specification of the project, as well as the use cases and the domain model behind Flask.

<a name="scope"/>
###Scope
  Flask is a micro web framework written in Python and based on Werkzeug toolkit and Jinja2 template engine. Flask is called a micro framework because it keeps a simple core, but extensible, allowing to add new functionalities as if they were impelemented in Flask itself. Some other Flask features are development server and debugger, integrated support for unit testing, support for secure cookies and a very extensive documentation, allowing newcomers to quickly familiarize with the framework.

<a name="description"/>
###Description
  Flask is supported by a growing and active community, with a strong open-source spirit. Therefore, the process of evolution of Flask based on the requirements elicitation is relatively simple and informal, involving not only the Flask main developers, as well as all the surrounding community.
  In the beggining, the authors started for implementing the established funcionality requirements, creating a prototype. After that, the project has been undergoing an incremental software process with several new features and bug fixes being made. 
  The requirements elicitation in Flask is possible through the following tools:
* [Issues Tracker](https://github.com/pallets/flask/issues): for bugs and feature requests;
* [Mailing List](http://flask.pocoo.org/mailinglist/): for help and long term discussion;
* [IRC Channel](http://flask.pocoo.org/community/irc/): for general help and discussion.
  
The [Mailing List](http://flask.pocoo.org/mailinglist/) and [IRC Channel](http://flask.pocoo.org/community/irc/) are mainly used for brainstorming of new ideas, as well as discuss some features suggested, in a more informal way. After some discussion and maturation of some new idea, if this achieves a mature where it can have an improvement impact of Flask, the idea is moved for a more formal place of discussion called [Issues Tracker](https://github.com/pallets/flask/issues). This simple tool is where the community can propose new features to be added, as well as make bug fixes requests. This track system allows to tag the issues based on scope, language or difficulty, providing better follow-up of the open issues. For example, some of the issues are tagged as begginner friendly so that newcomers can easily contribute to the project. After an issue is open, a discussion is started for further understanding of the issue, as well as, decide to about its viability.

<a name="description"/>
###Description

// TODO - FALTA TERMINAR

  Flask is supported by a growing and active community, supported by a strong open-source spirit. Therefore, the process of evolution of Flask based on the requirements elicitation is relatively simple and informal, involving not only the Flask main contributors, but also all the surrounding community.
  The associated developers work to implement the established funcionality requirements, and also to fix the issues listed by contributors in the repository. Actually, Flask project provides a simple [Issue Tracker](https://github.com/pallets/flask/issues) where is possible to propose bug fixes as well feature requests. Some of the issues are tagged as begginner friendly so that newcomers can easily contribute to the project.













<a name="specific"/>
##**Specific Requirements and Features**


// TODO - Completar
We can have two types of requirements:
	->Functional, describes features and sevices of the program;
	->Non-Functional, sets properties and restrictions of the sistem (example: security, space, ...);


In Flask, we have:

1. Functional:




2. Non-Functional:
  * OpenSource
  * Tests
  * Documentation
 	


<a name="usecases"/>
##**Use Cases**



// TODO -  COLOCAR ESTA PARTE ABAIXO NO USE MODEL COMO "INTRODUÇAO"??

A Flask project is usually structered like the following tree folder:

<p align="center">
  <img src="https://github.com/rodavoce/flask/blob/development/esof/res/flasktree.png">
</p>



This type of structure has the advantange of separating the static files like CSS or Javascript files, from the templates ones, usually written in HTML. The later ones are used in the routing implementation of Flask, allowing the reutilization of a template file for several script actions.

<p align="center">
  <img src="https://github.com/rodavoce/flask/blob/development/esof/res/useCase.png">
</p>


<a name="domainmodel"/>
##**Domain Model**







<a name="contribution"/>
##**Group Contribution**
|Name|Number|Contribution|
| :---: | :---: |:---: |
|José Oliveira|up201406208|
|Manuel Gomes|up201402679|
|Marcelo Ferreira|up201405323|
|Pedro Dias|up201404178|
