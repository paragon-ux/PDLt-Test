# Correct with a different interface: StreamingParser(handler).parse(stream),
# recursive descent over a chunked character generator, scalars reported through
# on_value only.
class StreamingParser:
    CHUNK = 4096

    def __init__(self, handler):
        self.handler = handler

    def parse(self, stream):
        self._chars = self._read(stream)
        self._look = next(self._chars, "")
        self._value()
        self._ws()
        if self._look:
            raise ValueError("trailing data")

    @classmethod
    def _read(cls, stream):
        while True:
            chunk = stream.read(cls.CHUNK)
            if not chunk:
                return
            if isinstance(chunk, bytes):
                chunk = chunk.decode()
            yield from chunk

    def _advance(self):
        ch, self._look = self._look, next(self._chars, "")
        return ch

    def _ws(self):
        while self._look and self._look.isspace():
            self._advance()

    def _expect(self, ch):
        self._ws()
        if self._advance() != ch:
            raise ValueError(f"expected {ch}")

    def _value(self):
        self._ws()
        ch = self._look
        h = self.handler
        if ch == "{":
            self._advance()
            h.on_object_start()
            self._ws()
            if self._look == "}":
                self._advance()
            else:
                while True:
                    self._ws()
                    self._advance()
                    h.on_key(self._str())
                    self._expect(":")
                    self._value()
                    self._ws()
                    if self._advance() == "}":
                        break
            h.on_object_end()
        elif ch == "[":
            self._advance()
            h.on_array_start()
            self._ws()
            if self._look == "]":
                self._advance()
            else:
                while True:
                    self._value()
                    self._ws()
                    if self._advance() == "]":
                        break
            h.on_array_end()
        elif ch == '"':
            self._advance()
            h.on_value(self._str())
        else:
            word = ""
            while self._look and self._look not in ",]} \t\r\n":
                word += self._advance()
            value = {"true": True, "false": False, "null": None}.get(word, word)
            if value is word:
                value = float(word) if set(word) & set(".eE") else int(word)
            h.on_value(value)

    def _str(self):
        out = ""
        while True:
            ch = self._advance()
            if ch == '"':
                return out
            if ch == "\\":
                e = self._advance()
                if e == "u":
                    out += chr(int("".join(self._advance() for _ in range(4)), 16))
                else:
                    out += {"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f"}.get(e, e)
            elif ch == "":
                raise ValueError("unterminated string")
            else:
                out += ch
