.. _caching-pattern:

캐싱(Caching)
=============

여러분의 어플리케이션이 느린 경우, 일종의 캐시를 넣어봐라.  그것이 
속도를 높이는 최소한의 가장 쉬운 방법이다.  캐시가 무엇을 하는가?
여러분이 수행을 마치는데 꽤 시간이 걸리는 함수를 갖고 있지만 결과가
실시간이 아닌 5분이 지난 결과도 괜찮다고 하자.  그렇다면 여러분은
그 시간동안 결과를 캐시에 넣어두고 사용해도 좋다는게 여기의 생각이다.

플라스크 그 자체는 캐시를 제공하지 않지만, 플라스크의 토대가 되는 
라이브러중 하나인 벡자이크(Werkzeug)는 굉장히 기본적인 캐시를 지원한다.
보통은 여러분이 memchached 서버로 사용하고 싶은 
다중 캐시 백엔드를 지원한다.

캐시 설정하기
-------------

여러분은 :class:`~flask.Flask` 을 생성하는 방법과 유사하게 캐시 객체를 
일단 생성하고 유지한다.  여러분이 개발 서버를 사용하고 있따면 여러분은
:class:`~werkzeug.contrib.cache.SimpleCache` 객체를 생성할 수 있고, 
그 객체는 파이썬 인터프리터의 메모리에 캐시의 항목을 저장하는 간단한 캐시다::

    from werkzeug.contrib.cache import SimpleCache
    cache = SimpleCache()

여러분이 memcached를 사용하고 싶다면, 지원되는 memcache 모듈중 하나를 갖고
(`PyPI <http://pypi.python.org/>`_ 에서 얻음) 어디선가 memcached 서버가 
동작하는 것을 보장해라.  그리고 나면 아래의 방식으로 memcached 서버에 
연결하면 된다::

    from werkzeug.contrib.cache import MemcachedCache
    cache = MemcachedCache(['127.0.0.1:11211'])

여러분이 App 엔진을 사용한다면, 손쉽게 App 엔진 ememcache 서버에 연결할
수 있다::

    from werkzeug.contrib.cache import GAEMemcachedCache
    cache = GAEMemcachedCache()

캐시 사용하기
-------------

Now how can one use such a cache?  There are two very important
operations: :meth:`~werkzeug.contrib.cache.BaseCache.get` and 
:meth:`~werkzeug.contrib.cache.BaseCache.set`.  This is how to use them:

To get an item from the cache call
:meth:`~werkzeug.contrib.cache.BaseCache.get` with a string as key name.
If something is in the cache, it is returned.  Otherwise that function
will return `None`::

    rv = cache.get('my-item')

To add items to the cache, use the :meth:`~werkzeug.contrib.cache.BaseCache.set`
method instead.  The first argument is the key and the second the value
that should be set.  Also a timeout can be provided after which the cache
will automatically remove item.

Here a full example how this looks like normally::

    def get_my_item():
        rv = cache.get('my-item')
        if rv is None:
            rv = calculate_value()
            cache.set('my-item', rv, timeout=5 * 60)
        return rv
