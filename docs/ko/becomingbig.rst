.. _becomingbig:

크게 만들기
===========

코드가 증가하고 어플리케이션의 규모가 커질 때 여러분에게 몇가지 선택사항이 있다.

소스 코드 읽기
--------------

플라스크는 이미 존재하고 잘 사용되는 도구인 벡자이크(WSGI)와 진자(템플릿 엔진)
의 상위에서 여러분 자신의 프레임워크를 만들기 위한 방법을 설명하기 위해 부분적으로
시작되었고, 개발되어오면서, 넓은 사용자층에게 유용해졌다. 여러분의 코드가 점점 
커진다면, 플라스크를 사용하지 않아야 한다 -- 그 이유를 이해해라.  소스를 읽어라.
플라스크의 소스는 읽혀지기 위해 쓰여진것이다; 그것은 공표된 문서이기에 여러분은
그것의 내부 API를 사용할 수 있다.  플라스크는 여러분의 프로젝트에 필요한 훅 포인트
(hook point)를 찾을 수 있도록 상위 라이브러리에 있는 문서화된 API를 고수하고 
그것의 내부 유틸리티를 문서화한다. 

훅(Hook). 확장하라.
-------------------

:ref:`api` 문서는 사용가능한 오버라이드, 훅 포인트, :ref:`signals` 로 가득 차 있다.
여러분은 요청과 응답 객체와 같은 것에 대한 커스텀 클래스를 제공할 수 있다. 여러분이 
사용하는 API에 대해 좀 더 깊게 파보고, 플라스크 릴리즈에 특별하게 사용가능한 
커스터마이징된 것을 찾아봐라.  여러분의 프로젝트가 여러 유틸리티나 플라스크 확장으로
리팩토링될 수 있는 방식을 찾아봐라.  커뮤니티에 있는 여러 
`확장 <http://flask.pocoo.org/extensions/>`_ 을 살펴보고 , 여러분이 필요한 도구를
찾을 수 없다면 여러분 자신의 확장을 만들기 위한 패턴을 찾아봐라.

Subclass.
---------

The :class:`~flask.Flask` class has many methods designed for subclassing. You
can quickly add or customize behavior by subclassing :class:`~flask.Flask` (see
the linked method docs) and using that subclass wherever you instantiate an
application class. This works well with :ref:`app-factories`.

Wrap with middleware.
---------------------

The :ref:`app-dispatch` chapter shows in detail how to apply middleware. You
can introduce WSGI middleware to wrap your Flask instances and introduce fixes
and changes at the layer between your Flask application and your HTTP
server. Werkzeug includes several `middlewares
<http://werkzeug.pocoo.org/docs/middlewares/>`_.

Fork.
-----

If none of the above options work, fork Flask.  The majority of code of Flask
is within Werkzeug and Jinja2.  These libraries do the majority of the work.
Flask is just the paste that glues those together.  For every project there is
the point where the underlying framework gets in the way (due to assumptions
the original developers had).  This is natural because if this would not be the
case, the framework would be a very complex system to begin with which causes a
steep learning curve and a lot of user frustration.

This is not unique to Flask.  Many people use patched and modified
versions of their framework to counter shortcomings.  This idea is also
reflected in the license of Flask.  You don't have to contribute any
changes back if you decide to modify the framework.

The downside of forking is of course that Flask extensions will most
likely break because the new framework has a different import name.
Furthermore integrating upstream changes can be a complex process,
depending on the number of changes.  Because of that, forking should be
the very last resort.

Scale like a pro.
-----------------

For many web applications the complexity of the code is less an issue than
the scaling for the number of users or data entries expected.  Flask by
itself is only limited in terms of scaling by your application code, the
data store you want to use and the Python implementation and webserver you
are running on.

Scaling well means for example that if you double the amount of servers
you get about twice the performance.  Scaling bad means that if you add a
new server the application won't perform any better or would not even
support a second server.

There is only one limiting factor regarding scaling in Flask which are
the context local proxies.  They depend on context which in Flask is
defined as being either a thread, process or greenlet.  If your server
uses some kind of concurrency that is not based on threads or greenlets,
Flask will no longer be able to support these global proxies.  However the
majority of servers are using either threads, greenlets or separate
processes to achieve concurrency which are all methods well supported by
the underlying Werkzeug library.

Discuss with the community.
---------------------------

The Flask developers keep the framework accessible to users with codebases big
and small. If you find an obstacle in your way, caused by Flask, don't hesitate
to contact the developers on the mailinglist or IRC channel.  The best way for
the Flask and Flask extension developers to improve the tools for larger
applications is getting feedback from users.
