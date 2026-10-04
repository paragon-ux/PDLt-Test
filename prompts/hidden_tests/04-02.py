"""Hidden tests for 04-02: a SAX-style streaming JSON parser.

From the prompt:
- parse(stream, handler) reads a file-like object one chunk at a time;
- the handler gets on_object_start/end, on_array_start/end, on_key, on_value,
  on_string, on_number, on_bool and on_null;
- string escapes (\\\\, \\n, \\t, \\", \\uXXXX) are decoded;
- nesting depth is arbitrary.

The prompt lists both on_value and the typed scalar callbacks without saying
which fire. Each consistent reading passes: scalars from on_value, from the
typed callbacks, or from whichever of the two fires; a key may also be echoed
through on_string. Other on_* calls are ignored.

"One chunk at a time" is checked as: the parser never asks the stream for
everything (read() or read(-1), readline() without a size, readlines(), or line
iteration). A text stream is tried first, then a binary one.

The entry point is a two-argument function, or a class used as
Class().parse(stream, handler), Class(handler).parse(stream) or
Class(stream, handler).parse().
"""
TEST_SECONDS = 30


def CANDIDATES():
    named = list(functions_named("parse", "parse_json", "stream_parse", "parse_stream", "streaming_parse",
                                 "sax_parse", "parse_json_stream"))
    methods = [_class_adapter(cls) for cls in classes_with("parse") if not _is_handler(cls)]
    others = [f for f in functions_named("parse", params=2) if f not in named]
    return named + methods + others


def _is_handler(cls):
    return callable(getattr(cls, "on_object_start", None)) and not callable(getattr(cls, "feed", None))


def _required(fn, skip_self):
    import inspect

    try:
        params = list(inspect.signature(fn).parameters.values())
    except (TypeError, ValueError):
        return None
    if skip_self and params and params[0].name == "self":
        params = params[1:]
    return [p.name.lower() for p in params if p.default is p.empty and p.kind in (p.POSITIONAL_ONLY,
                                                                                    p.POSITIONAL_OR_KEYWORD)]


def _class_adapter(cls):
    def parse(stream, handler):
        init = _required(cls.__init__, True) if cls.__init__ is not object.__init__ else []
        if not init:
            return cls().parse(stream, handler)
        if len(init) == 1:
            if "stream" in init[0] or "file" in init[0] or "source" in init[0]:
                return cls(stream).parse(handler)
            return cls(handler).parse(stream)
        if "handler" in init[0] or "callback" in init[0]:
            return cls(handler, stream).parse()
        return cls(stream, handler).parse()

    parse.__name__ = f"{cls.__name__}.parse"
    return parse


_STRUCT = {"on_object_start": ("{",), "on_object_end": ("}",), "on_array_start": ("[",), "on_array_end": ("]",)}


def _scalar(value):
    if value is None:
        return ("null",)
    if isinstance(value, bool):
        return ("bool", value)
    if isinstance(value, (int, float)):
        return ("num", float(value))
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    if isinstance(value, str):
        return ("str", value)
    return ("other", repr(value))


class _Recorder:
    def __init__(self):
        self.events = []

    def __getattr__(self, name):
        if not name.startswith("on_"):
            raise AttributeError(name)

        def record(*args, **kwargs):
            value = args[0] if args else (next(iter(kwargs.values())) if kwargs else None)
            self.events.append((name, value))

        return record


_TYPED = ("on_string", "on_number", "on_bool", "on_null")


def _normalize(events, scalars, key_echo):
    """The events under one reading of the callback contract.

    ``scalars``: "value" reads scalars from on_value only, "typed" from the typed
    callbacks only, "either" from both (each scalar fires exactly one of them).
    ``key_echo``: an on_string right after on_key with the same text is the key
    reported twice, not a value.
    """
    out, last = [], None
    for name, value in events:
        if name in _STRUCT:
            out.append(_STRUCT[name])
        elif name == "on_key":
            out.append(("key",) + _scalar(value)[1:])
        elif name == "on_string" and key_echo and last == "on_key" and out[-1][1:] == _scalar(value)[1:]:
            pass
        elif name == "on_value" and scalars in ("value", "either"):
            out.append(_scalar(value))
        elif name in _TYPED and scalars in ("typed", "either"):
            out.append(_scalar(None if name == "on_null" else value))
        last = name
    return out


def _matches(events, expected):
    return any(_normalize(events, scalars, echo) == expected
               for scalars in ("value", "typed", "either") for echo in (False, True))


def _expected(value):
    if isinstance(value, dict):
        events = [("{",)]
        for k, v in value.items():
            events.append(("key", k))
            events.extend(_expected(v))
        return events + [("}",)]
    if isinstance(value, list):
        events = [("[",)]
        for v in value:
            events.extend(_expected(v))
        return events + [("]",)]
    return [_scalar(value)]


def _streams():
    import io

    class Text(io.StringIO):
        unbounded = False

        def read(self, size=-1):
            if size is None or size < 0:
                type(self).unbounded = True
            return super().read(size)

        def readline(self, size=-1):
            if size is None or size < 0:
                type(self).unbounded = True
            return super().readline(size)

        def readlines(self, hint=-1):
            type(self).unbounded = True
            return super().readlines(hint)

        def __iter__(self):
            type(self).unbounded = True
            return super().__iter__()

    class Binary(io.BytesIO):
        unbounded = False

        def read(self, size=-1):
            if size is None or size < 0:
                type(self).unbounded = True
            return super().read(size)

        def read1(self, size=-1):
            if size is None or size < 0:
                type(self).unbounded = True
            return super().read1(size)

        def readline(self, size=-1):
            if size is None or size < 0:
                type(self).unbounded = True
            return super().readline(size)

        def readlines(self, hint=-1):
            type(self).unbounded = True
            return super().readlines(hint)

        def __iter__(self):
            type(self).unbounded = True
            return super().__iter__()

    return Text, Binary


def _run(f, text):
    """Raw events from parsing ``text``, and whether the parser read it all at once."""
    Text, Binary = _streams()
    errors = []
    for make in (lambda: Text(text), lambda: Binary(text.encode("utf-8"))):
        stream, handler = make(), _Recorder()
        type(stream).unbounded = False
        try:
            f(stream, handler)
        except Exception as exc:  # noqa: BLE001 - the binary form is tried next
            errors.append(f"{type(exc).__name__}: {exc}")
            continue
        return handler.events, type(stream).unbounded
    raise AssertionError("; ".join(errors)[:300])


DOC = ('{"name": "stream", "values": [1, -2.5, 3e2, 0, true, false, null],'
       ' "text": "q\\"uote \\\\ back\\nnew\\ttab \\u00e9\\u4e2d",'
       ' "nested": {"a": {"b": {"c": [[[]], {}]}}}, "empty": "", "neg": -0.125}')


def test_events_for_a_mixed_document(f):
    import json

    events, _ = _run(f, DOC)
    assert _matches(events, _expected(json.loads(DOC))), events[:40]


def test_deep_nesting(f):
    import json

    text = "[" * 200 + "1" + "]" * 200
    events, _ = _run(f, text)
    assert _matches(events, _expected(json.loads(text)))
    text = '{"k":' * 150 + '"v"' + "}" * 150
    events, _ = _run(f, text)
    assert _matches(events, _expected(json.loads(text)))


def test_thousand_element_array_streams(f):
    import json

    text = json.dumps([{"id": i, "ok": i % 2 == 0, "tag": f"t{i}"} for i in range(1000)])
    events, unbounded = _run(f, text)
    assert _matches(events, _expected(json.loads(text)))
    assert not unbounded, "the parser asked the stream for all of its contents at once"


def test_insignificant_whitespace(f):
    import json

    for text in (' \n [ 1 , "a" ,\t{ } ] \n', '{ "a" :[ ] ,"b":{"c" : null }}'):
        events, _ = _run(f, text)
        assert _matches(events, _expected(json.loads(text))), (text, events)


TESTS = [test_events_for_a_mixed_document, test_deep_nesting, test_thousand_element_array_streams,
         test_insignificant_whitespace]
