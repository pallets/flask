from base64 import b64decode, b64encode
from datetime import datetime
from uuid import UUID

from jinja2 import Markup
from werkzeug.http import http_date, parse_date

from flask._compat import iteritems, text_type
from flask.json import dumps, loads


class JSONTag(object):
    __slots__ = ()
    key = None

    def check(self, serializer, value):
        raise NotImplementedError

    def to_json(self, serializer, value):
        raise NotImplementedError

    def to_python(self, serializer, value):
        raise NotImplementedError

    def tag(self, serializer, value):
        return {self.key: self.to_json(serializer, value)}


class TagDict(JSONTag):
    __slots__ = ()
    key = ' di'

    def check(self, serializer, value):
        return isinstance(value, dict)

    def to_json(self, serializer, value, key=None):
        if key is not None:
            return {key + '__': serializer._tag(value[key])}

        return dict((k, serializer._tag(v)) for k, v in iteritems(value))

    def to_python(self, serializer, value):
        key = next(iter(value))
        return {key[:-2]: value[key]}

    def tag(self, serializer, value):
        if len(value) == 1:
            key = next(iter(value))

            if key in serializer._tags:
                return {self.key: self.to_json(serializer, value, key=key)}

        return self.to_json(serializer, value)


class TagTuple(JSONTag):
    __slots__ = ()
    key = ' t'

    def check(self, serializer, value):
        return isinstance(value, tuple)

    def to_json(self, serializer, value):
        return [serializer._tag(item) for item in value]

    def to_python(self, serializer, value):
        return tuple(value)


class PassList(JSONTag):
    __slots__ = ()

    def check(self, serializer, value):
        return isinstance(value, list)

    def to_json(self, serializer, value):
        return [serializer._tag(item) for item in value]

    tag = to_json


class TagBytes(JSONTag):
    __slots__ = ()
    key = ' b'

    def check(self, serializer, value):
        return isinstance(value, bytes)

    def to_json(self, serializer, value):
        return b64encode(value).decode('ascii')

    def to_python(self, serializer, value):
        return b64decode(value)


class TagMarkup(JSONTag):
    __slots__ = ()
    key = ' m'

    def check(self, serializer, value):
        return callable(getattr(value, '__html__', None))

    def to_json(self, serializer, value):
        return text_type(value.__html__())

    def to_python(self, serializer, value):
        return Markup(value)


class TagUUID(JSONTag):
    __slots__ = ()
    key = ' u'

    def check(self, serializer, value):
        return isinstance(value, UUID)

    def to_json(self, serializer, value):
        return value.hex

    def to_python(self, serializer, value):
        return UUID(value)


class TagDateTime(JSONTag):
    __slots__ = ()
    key = ' d'

    def check(self, serializer, value):
        return isinstance(value, datetime)

    def to_json(self, serializer, value):
        return http_date(value)

    def to_python(self, serializer, value):
        return parse_date(value)


class TaggedJSONSerializer(object):
    __slots__ = ('_tags', '_order')
    _default_tags = [
        TagDict(), TagTuple(), PassList(), TagBytes(), TagMarkup(), TagUUID(),
        TagDateTime(),
    ]

    def __init__(self):
        self._tags = {}
        self._order = []

        for tag in self._default_tags:
            self.register(tag)

    def register(self, tag, force=False, index=-1):
        key = tag.key

        if key is not None:
            if not force and key in self._tags:
                raise KeyError("Tag '{0}' is already registered.".format(key))

            self._tags[key] = tag

        if index == -1:
            self._order.append(tag)
        else:
            self._order.insert(index, tag)

    def _tag(self, value):
        for tag in self._order:
            if tag.check(self, value):
                return tag.tag(self, value)

        return value

    def _untag(self, value):
        if len(value) != 1:
            return value

        key = next(iter(value))

        if key not in self._tags:
            return value

        return self._tags[key].to_python(self, value[key])

    def dumps(self, value):
        return dumps(self._tag(value), separators=(',', ':'))

    def loads(self, value):
        return loads(value, object_hook=self._untag)
