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

서브클래스.
-----------

:class:`~flask.Flask` 클래스는 서브클래싱에 대해 설계된 여러 메소드가 있다.
여러분은 :class:`~flask.Flask` (연결된 메소드 문서를 살펴봐라) 를 
서브클래싱하고 어플리케이션 클래스를 인스턴스화한 곳 어디서나 그 서브클래스를 
사용하여 동작을 빠르게 추가하거나 커스터마이징할 수 있다.  이것은 
:ref:`app-factories` 과 함께 잘 동작한다.

미들웨어로 감싸기.
---------------------

:ref:`app-dispatch` 장에서 미들웨어를 적용하는 방법에 대해 자세히 보여줬다.
여러분의 플라스크 인스턴스를 감싸기 위해 WSGI 미들웨어와 여러분의 어플리케이션
과 HTTP 서버 사이에 있는 계층에 수정과 변경을 소개할 수 있다. 벡자이크는 
다수의 `미들웨어 <http://werkzeug.pocoo.org/docs/middlewares/>`_ 를 포함하고 있다.

분기하기.
---------

위에서 언급한 선택사항 중 어느 것에도 해당되지 않는다면, 플라스크를 분기해라.
플라스크 코드의 다수는 벡자이크와 진자2 안에 있는 것이다.  이런 라이브러리가
그 동작의 대다수를 수행한다.  플라스크는 단지 그런 라이브러리를 잘 붙여논
풀같은 것이다.  모든 프로젝트에 대해 하부 프레임워크가 방해가 되는 점이 있다
(왜냐하면 원 개발자들의 가진 가정들 때문에).  이것은 자연스러운 것인데 왜냐하면
그런 경우가 아니라면, 그 프레임워크는 시작부터 굉장히 가파른 학습 곡선과 많은
개발자의 좌절감을 유발하는 매우 복잡한 시스템이 될것이기 때문이다.

이것은 플라스크에만 유일하게 적용되지 않는다.  많은 사람들이 그들이 사용하는
프레임워크의 단점에 대응하기 위해 패치되고 변경된 버전의 프레임워크를 사용한다.
이 방식 또한 플라스크의 라이선스에 반영돼있다.  여러분이 플라스크에 변경하기로 
결정했더라도 그 어떤 변경에 대해서도 다시 기여하지 않아도 된다.

물론 분기하는 것에 단점은 플라스크 확장에 대부분 깨질것이라는 점인데
왜냐하면 새로운 프레임워크는 다른 임포트 명을 가질 것이기 때문이다.
더 나아가서 변경의 개수의 따라 상위 변경을 통합하는 것이 복합한 과정일 
수 있다.  그런것 때문에 분기하는 것은 최후의 보루가 되어야 할 것이다.

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
