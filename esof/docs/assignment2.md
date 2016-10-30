![FEUP image](https://sigarra.up.pt/feup/pt/WEB_GESSI_DOCS.download_file?p_name=F-370784536/logo_cores_oficiais.jpg)
#**Requirements Elicitation**

##**Integrated Masters in Informatics and Computer Engineering**

![flask image](http://flask.pocoo.org/static/logo/flask.png)

<a name="index"/>
##**Index**
1. [Requirements elicitation](#elicitation)
  * [Introduction](#introduction)
  * [Purpose](#purpose)
  * [Scope](#scope)
  * [Description](#description)
2. [Requirements specification and Features](#specific)
3. [Use Cases](#usecases)
4. [Domain Model](#domainmodel)
5. [Group Contribution](#contribution)

<a name="elicitation"/>
##**Requirements Elicitation**
<a name="introduction"/>
###Introduction
***Software Requirements*** is a field within software engineering that deals with establishing the needs of stakeholders that are to be solved by software. The ***IEEE Standard Glossary of Software Engineering Terminology*** defines a requirement as:
* A condition or capability needed by a user to solve a problem or achieve an objective;
* A condition or capability that must be met or possessed by a system or system component to satisfy a specification, or other formally imposed document.

In requirements engineering, ***requirements elicitation*** is the practice of collecting the requirements of a system from users, customers and others stakeholders. Before requirements can be analyzed, modeled, or specified, they must be gathered through an elicitation process.
***Requirements elicitation*** and ***analysis*** involves collecting as many potential requirements as possible, then refining them to form a complete, concise and consistent set of high-quality requirements, and then analyzing them to start forming a preliminary set of features to be developed. 
The most common practices used in ***requirements elicitation*** includes interviews, questionnaires, user observation, workshops, brainstorming, use cases, role playing and prototyping.

<a name="purpose"/>
###Purpose
  The purpose of this document is to provide a quick overview of the funcionality of Flask in particular for developers and stackholders. The document will particulary detail the requirements elicitation and specification of the project, as well as the use cases and the domain model behind Flask.

<a name="scope"/>
###Scope
  Flask is a micro web framework written in Python and based on Werkzeug toolkit and Jinja2 template engine. Flask is called a micro framework because it keeps a simple core, but extensible, allowing to add new functionalities as if they were impelemented in Flask itself.

<a name="description"/>
###Description
  Flask is supported by a growing and active community, with a strong open-source spirit. Therefore, the process of evolution of Flask based on the requirements elicitation is relatively simple and informal, involving not only the Flask core developers, as well as all the surrounding community.
  In the beggining, the authors started for implementing the established funcionality requirements, creating a prototype. After that, the project has been undergoing an incremental software process with several new features and bug fixes being made. 
  The ***requirements elicitation*** in Flask is possible through the following tools:
* [Issues Tracker](https://github.com/pallets/flask/issues): for bugs and feature requests;
* [Mailing List](http://flask.pocoo.org/mailinglist/): for help and long term discussion;
* [IRC Channel](http://flask.pocoo.org/community/irc/): for general help and discussion.
  
The [Mailing List](http://flask.pocoo.org/mailinglist/) and [IRC Channel](http://flask.pocoo.org/community/irc/) are mainly used for brainstorming of new ideas, as well as discuss some features suggested, in a more informal way. After some discussion and maturation of some new idea, if this achieves a mature where it can have an improvement impact of Flask, the idea is moved for a more formal place of discussion called [Issues Tracker](https://github.com/pallets/flask/issues). This simple tool is where the community can propose new features to be added, as well as make bug fixes requests. This track system allows to tag the issues based on scope, language or difficulty, providing a better follow-up of the open issues. For example, some of the issues are tagged as begginner friendly so that newcomers can easily contribute to the project. After an issue is open, a discussion is started for further understanding of the issue, as well as, decide about its viability.
In case some issue is decided to be implemented, anyone in the community can contribute in this step.

<a name="specific"/>
##**Requirements Specification and Features**
A ***software requirements specification (SRS)*** is a description of a software system to be developed. It lays out functional and non-functional requirements, and may include a set of use cases that describe user interactions that the software must provide.
A brief description of the differences between funcional and non-functional requirements is provided below:
*  ***Functional***: describes what the system must do. They can often be derived from "stories" about how the system will be used, which may be in the form of scenarios, use-cases, or just a simple description of operations;
*  ***Non-Functional***: describes other properties or characteristics that the system must have, other than its basic functionality. Because non-functional requirements are generally more difficult to identify, checklists of some kind are often used to make sure that developers consider all possibilities and do not leave out anything important.

The ***software requirements specification*** document enlists enough and necessary requirements that are required for the project development. To derive the requirements becomes necessary to have clear and thorough understanding of the products to be developed or being developed. This is achieved and refined with detailed and continuous communications with the project team and customer until the completion of the software.


Although Flask doesn't own a ***SRS***, it has a lot of documentation supporting the operation of the framework, helping developers and contributors to better undertanding the functionalities of Flask.
About the functional and non-functional requirements, the following can be found in Flask:

* ***Functional***:
  *  Provides an extendable core of functionality;
  *  Routing for selection of paths of the network;
  *  Takes the data from the Database (by querying it with SQL) and put the acquired information into other formats (by using Jinja 2) that can actually be used by a browser to display the web site.

* ***Non-Functional***:
  * Open source;
  * Tests;
  * Documentation;
  * Support for secure cookies;  
  * RESTful request dispatching;
  * WSGI compliant;
  * Compatible with Python;
  * Unicode based.

<a name="usecases"/>
##**Use Cases**


A Flask project is usually structered like the following tree folder:

<p align="center">
  <img src="https://github.com/rodavoce/flask/blob/development/esof/res/flasktree.png">
</p>



This type of structure has the advantange of separating the static files like CSS or Javascript files, from the templates ones, usually written in HTML. The later ones are used in the routing implementation of Flask, allowing the reutilization of a template file for several script actions.

<p align="center">
  <img src="https://github.com/rodavoce/flask/blob/development/esof/res/ext.png">
</p>

**User case** :  Install Extensions

**Actors**: Developer

**Goal description**: Add aditional features to Flask framework

**Reference to Requirements**:
	
**Pre-conditions**: Extensions should be compatible with Flask version used

**Description**: 
	1. The developer need to solve a problem that Flask core doesn’t solve
	2. He search and install  a developed solution.
 
**Post-conditions**:

1.  System will have the package installed.

**Variations**:

**Exceptions**:

<p align="center">
  <img src="https://github.com/rodavoce/flask/blob/development/esof/res/test.png">
</p>

**User Case**: Test in built-in development server 

**Actors**: Developer

**Goal description**: Test developed project in local machine 

**Reference to Requirements**:

**Pre-conditions**:

**Description** 
	1. Developer has a prototype to test.
	2. The prototype is loaded into the server.
	3. Developer  interact with prototype.

**Post-conditions**:

**Variations**:

**Exceptions**:

**User Case **: User server debug mode

**Actors**: Developer

**Goal description**:

**Reference to Requirements**:

**Pre-conditions**:

**Description**:

**Post-conditions**:

**Variations**:

**Exceptions**:

**User Case** : Run automated Test

**Actors**: Developer

**Goal description**:

**Reference to Requirements**:

**Pre-conditions**:

**Description**:

**Post-conditions**:

**Variations**:

**Exceptions**:


**User Case **: Implement automated test

**Actors**: Developer

**Goal description**:

**Reference to Requirements**:

**Pre-conditions**:

**Description**:

**Post-conditions**:

**Variations**:

**Exceptions**:


<p align="center">
  <img src="https://github.com/rodavoce/flask/blob/development/esof/res/dev.png">
</p>

**User Case **: Develop or Build  Project !?!
**Actors**: Developer
**Goal description**:   Make the desired product !?!
**Reference to Requirements**:
**Pre-conditions**:
**Description**:
	 The develpor has set the requirements for his project and started using Flask features.  
**Post-conditions**:
**Variations**:
	The developer  fixing or upgrading the project.
**Exceptions**:



**User Case** :  Route URL’s
**Actors**: Developer
**Goal description**:   Beautify and make more user friendly URL’s
**Reference to Requirements**:
**Pre-conditions**:
**Description**:
	 The develpor has made a set  of rule to determinate URL’s  to make them user friendly
**Post-conditions**:
**Variations**:
**Exceptions**:

**User Case**:  Set Application context
**Actors**: Developer
**Goal description**:  Define  one or more applications that in run in this python process
**Reference to Requirements**:
**Pre-conditions**:
**Description**:
	 The develpor create a certain number of applications context 
**Post-conditions**:
**Variations**:
**Exceptions**:


**User Case**:  Set Templates
**Actors**: Developer
**Goal description**:   Define multiple HTML  templates   
**Reference to Requirements**:
**Pre-conditions**:
**Description**:
	 The developer made  HTML templates to use. 
**Post-conditions**:
**Variations**:
**Exceptions**:


**User Case** :  Set Signals & handlers  (MUDAR NA IMAGEM )
**Actors**: Developer
**Goal description**:   Define applicantions subscriptions
**Reference to Requirements**:
**Pre-condition**s:
**Description**:
	The developer set applications subscriptions like email notifications or temporary subscriptions in interactions between server and application.
**Post-conditions**:
**Variations**:
**Exceptions**:



**User Case** :  Set Database 
**Actors**: Developer
**Goal description**:   Structure the database
**Reference to Requirements**:
**Pre-conditions**:
**Description**:
	The developer choose the database type and structure has we likes.
**Post-conditions**:
**Variations**:
**Exceptions**:


**User Case** :  Set Views 
**Actors**: Developer
**Goal description**: Define pre-consults to the database
**Reference to Requirements**:
**Pre-conditions**:
**Description**:  The developer choose how to expose the data in the database
**Post-conditions**:
**Variations**:
**Exceptions**:


**User Case** :  Define user previleges 
**Actors**: Developer
**Goal description**:  Set what a user can do.
**Reference to Requirements**:
**Pre-conditions**:
**Description**:  The developer choose what  a  type of user can do in the application 
**Post-conditions**:
**Variations**:
**Exceptions**:


**User Case**:  Set request object ( MUDAR O SET COOKIE )
**Actors**: Developer
**Goal description**: Define  user  local data that is sent to server
**Reference to Requirements**:
**Pre-conditions**:
**Description**:  The developer set what information  from user data is storaged and send 
	   that  to server as forms, cookies , files or other things
**Post-conditions**:
**Variations**:
**Exceptions**:

**User Case** :  Set sessions 
**Actors**: Developer
**Goal description**:
**Reference to Requirements**:
**Pre-conditions**:
**Description**:
**Post-conditions**:
**Variations**:
**Exceptions**:


**User Case** :  Set request context 
**Actors**: Developer
**Goal description**: Define what resources the aplication context need.
**Reference to Requirements**:
**Pre-conditions**:
**Description**:  The developer analyse and set what are the resources used by the application.
**Post-conditions**:
**Variations**:
**Exceptions**:

<a name="domainmodel"/>
##**Domain Model**


  <img src="https://github.com/rodavoce/flask/blob/development/esof/res/domain_model_1st_sketch.png">





<a name="contribution"/>
##**Group Contribution**
|Name|Number|Contribution|
| :---: | :---: |:---: |
|José Oliveira|up201406208|
|Manuel Gomes|up201402679|
|Marcelo Ferreira|up201405323|
|Pedro Dias|up201404178|
