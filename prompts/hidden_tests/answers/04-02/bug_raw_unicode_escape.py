# Wrong: \uXXXX escapes are kept as literal text instead of decoded.
class JSONSyntaxError(ValueError):
    pass


class _Chars:
    """Characters from a stream read in fixed-size chunks, with one-char lookahead."""

    def __init__(self, stream, chunk_size=64):
        self.stream, self.chunk_size = stream, chunk_size
        self.buf, self.pos = "", 0

    def peek(self):
        if self.pos >= len(self.buf):
            chunk = self.stream.read(self.chunk_size)
            if isinstance(chunk, bytes):
                chunk = chunk.decode("utf-8")
            self.buf, self.pos = chunk, 0
            if not chunk:
                return ""
        return self.buf[self.pos]

    def next(self):
        ch = self.peek()
        self.pos += 1
        return ch

    def skip_ws(self):
        while self.peek() in " \t\r\n" and self.peek():
            self.pos += 1


_ESCAPES = {'"': '"', "\\": "\\", "/": "/", "b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t"}


def _string(chars):
    out = []
    while True:
        ch = chars.next()
        if ch == "":
            raise JSONSyntaxError("unterminated string")
        if ch == '"':
            return "".join(out)
        if ch == "\\":
            esc = chars.next()
            if esc == "u":
                out.append('\\u' + "".join(chars.next() for _ in range(4)))
            elif esc in _ESCAPES:
                out.append(_ESCAPES[esc])
            else:
                raise JSONSyntaxError(f"bad escape {esc!r}")
        else:
            out.append(ch)


def _literal(chars):
    text = []
    while chars.peek() and chars.peek() not in " \t\r\n,]}:":
        text.append(chars.next())
    word = "".join(text)
    if word == "true":
        return True
    if word == "false":
        return False
    if word == "null":
        return None
    try:
        return float(word) if any(c in word for c in ".eE") else int(word)
    except ValueError:
        raise JSONSyntaxError(f"bad literal {word!r}") from None


def _emit_scalar(handler, value):
    handler.on_value(value)
    if value is None:
        handler.on_null()
    elif isinstance(value, bool):
        handler.on_bool(value)
    elif isinstance(value, str):
        handler.on_string(value)
    else:
        handler.on_number(value)


def parse(stream, handler):
    """Iterative: the only state kept is a stack of open containers."""
    chars = _Chars(stream)
    stack = []  # entries: ["obj" | "arr", expecting]
    expect_value = True
    while True:
        chars.skip_ws()
        ch = chars.peek()
        if ch == "":
            if stack or expect_value:
                raise JSONSyntaxError("unexpected end of input")
            return
        if expect_value:
            chars.next()
            if ch == "{":
                handler.on_object_start()
                stack.append("obj")
                chars.skip_ws()
                if chars.peek() == "}":
                    chars.next()
                    stack.pop()
                    handler.on_object_end()
                    expect_value = False
                    continue
                chars.skip_ws()
                if chars.next() != '"':
                    raise JSONSyntaxError("expected key")
                handler.on_key(_string(chars))
                chars.skip_ws()
                if chars.next() != ":":
                    raise JSONSyntaxError("expected ':'")
                continue
            if ch == "[":
                handler.on_array_start()
                stack.append("arr")
                chars.skip_ws()
                if chars.peek() == "]":
                    chars.next()
                    stack.pop()
                    handler.on_array_end()
                    expect_value = False
                continue
            if ch == '"':
                _emit_scalar(handler, _string(chars))
            else:
                chars.pos -= 1
                _emit_scalar(handler, _literal(chars))
            expect_value = False
            continue
        if not stack:
            raise JSONSyntaxError(f"trailing data {ch!r}")
        chars.next()
        if ch == ",":
            expect_value = True
            if stack[-1] == "obj":
                chars.skip_ws()
                if chars.next() != '"':
                    raise JSONSyntaxError("expected key")
                handler.on_key(_string(chars))
                chars.skip_ws()
                if chars.next() != ":":
                    raise JSONSyntaxError("expected ':'")
        elif ch == "}" and stack[-1] == "obj":
            stack.pop()
            handler.on_object_end()
        elif ch == "]" and stack[-1] == "arr":
            stack.pop()
            handler.on_array_end()
        else:
            raise JSONSyntaxError(f"unexpected {ch!r}")


class Handler:
    def on_object_start(self): pass
    def on_object_end(self): pass
    def on_array_start(self): pass
    def on_array_end(self): pass
    def on_key(self, key): pass
    def on_value(self, value): pass
    def on_string(self, s): pass
    def on_number(self, n): pass
    def on_bool(self, b): pass
    def on_null(self): pass
