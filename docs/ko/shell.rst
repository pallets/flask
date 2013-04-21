.. _shell:

쉘에서 작업하기
======================

.. versionadded:: 0.3

많은 사람들이 파이썬을 좋아하는 이유 중 한가지는 바로 대화식 쉘이다.
그것은 기본적으로 여러분이 실시간으로 파이썬 명령을 싱행하고 결과를 실시간으로 
즉시 받아 볼 수 있다. Flask 자체는 대화식 쉘과 함께 제공되지 않는다. 왜냐하면 
Flask는 특정한 선행 작업이 필요하지 않고, 단지 여러분의 어플리케이션에서 불러오기만 하면 
시작할 수 있기 때문이다.


하지만, 쉘에서 좀 더 많은 즐거운 경험을 얻을 수 있는 몇 가지 유용한 헬퍼들이 있다.
대화식 콘솔 세션에서의 가장 중요한 문제는 여러분이 직접 브라우저에서 처럼 
:data:`~flask.g`, :data:`~flask.request` 를 발생 시킬 수 없고,  
 그 밖의 다른 것들도 가능하지 않다. 하지만 테스트 해야 할 코드가 그것들에게
종속관계에 있다면 여러분은 어떻게 할 것인가?


이 장에는 몇가지 도움이 되는 함수가 있다. 
이 함수들은 대화식 쉘에서의 사용뿐만 아니라, 단위테스트와 같은 그리고 요청 컨텍스트를 
위조해야 하는 상황에서 또한 유용하다는 것을 염두해 두자.


일반적으로 여러분이 :ref:`request-context` 를 먼저 읽기를 권장한다.


요청 컨텍스트 생성하기
--------------------------

The easiest way to create a proper request context from the shell is by
using the :attr:`~flask.Flask.test_request_context` method which creates
us a :class:`~flask.ctx.RequestContext`:

>>> ctx = app.test_request_context()

Normally you would use the `with` statement to make this request object
active, but in the shell it's easier to use the
:meth:`~flask.ctx.RequestContext.push` and
:meth:`~flask.ctx.RequestContext.pop` methods by hand:

>>> ctx.push()

From that point onwards you can work with the request object until you
call `pop`:

>>> ctx.pop()

Firing Before/After Request
---------------------------

By just creating a request context, you still don't have run the code that
is normally run before a request.  This might result in your database
being unavailable if you are connecting to the database in a
before-request callback or the current user not being stored on the
:data:`~flask.g` object etc.

This however can easily be done yourself.  Just call
:meth:`~flask.Flask.preprocess_request`:

>>> ctx = app.test_request_context()
>>> ctx.push()
>>> app.preprocess_request()

Keep in mind that the :meth:`~flask.Flask.preprocess_request` function
might return a response object, in that case just ignore it.

To shutdown a request, you need to trick a bit before the after request
functions (triggered by :meth:`~flask.Flask.process_response`) operate on
a response object:

>>> app.process_response(app.response_class())
<Response 0 bytes [200 OK]>
>>> ctx.pop()

The functions registered as :meth:`~flask.Flask.teardown_request` are
automatically called when the context is popped.  So this is the perfect
place to automatically tear down resources that were needed by the request
context (such as database connections).


Further Improving the Shell Experience
--------------------------------------

If you like the idea of experimenting in a shell, create yourself a module
with stuff you want to star import into your interactive session.  There
you could also define some more helper methods for common things such as
initializing the database, dropping tables etc.

Just put them into a module (like `shelltools` and import from there):

>>> from shelltools import *
