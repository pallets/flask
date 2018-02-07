from datetime import datetime
from uuid import uuid4

import pytest

from flask import Markup
from flask.json.tag import TaggedJSONSerializer, JSONTag


@pytest.mark.parametrize("data", (
    {' t': (1, 2, 3)},
    {' t__': b'a'},
    {' di': ' di'},
    {'x': (1, 2, 3), 'y': 4},
    (1, 2, 3),
    [(1, 2, 3)],
    b'\xff',
    Markup('<html>'),
    uuid4(),
    datetime.utcnow().replace(microsecond=0),
))
def test_dump_load_unchanged(data):
    s = TaggedJSONSerializer()
    assert s.loads(s.dumps(data)) == data


def test_duplicate_tag():
    class TagDict(JSONTag):
        key = ' d'

    s = TaggedJSONSerializer()
    pytest.raises(KeyError, s.register, TagDict)
    s.register(TagDict, force=True, index=0)
    assert isinstance(s.tags[' d'], TagDict)
    assert isinstance(s.order[0], TagDict)


def test_custom_tag():
    class Foo(object):
        def __init__(self, data):
            self.data = data

    class TagFoo(JSONTag):
        __slots__ = ()
        key = ' f'

        def check(self, value):
            return isinstance(value, Foo)

        def to_json(self, value):
            return self.serializer.tag(value.data)

        def to_python(self, value):
            return Foo(value)

    s = TaggedJSONSerializer()
    s.register(TagFoo)
    assert s.loads(s.dumps(Foo('bar'))).data == 'bar'


def test_tag_interface():
    t = JSONTag(None)
    pytest.raises(NotImplementedError, t.check, None)
    pytest.raises(NotImplementedError, t.to_json, None)
    pytest.raises(NotImplementedError, t.to_python, None)
