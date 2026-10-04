"""Hidden tests for 06-07: the encoding round trip, fixed.

Candidates pair a save function (text, filepath) with a load function
(filepath), names that say "fixed" (or similar) first. A deliverable may keep
the originals.

Text saved and loaded back must be identical for:
- Latin text with accents;
- CJK;
- emoji, including characters outside the Basic Multilingual Plane;
- an empty string.

Any encoding that round-trips all of Unicode passes, used consistently by both
functions. Files are written in the sandbox's working directory.
"""
TEST_SECONDS = 20
_PREFER = ("fix", "correct", "safe", "utf", "new")


class _Pair:
    def __init__(self, save, load):
        self.save, self.load = save, load
        self.__name__ = f"{save.__name__}/{load.__name__}"


def CANDIDATES():
    saves = [f for f in functions_named("save_to_file", params=2) if any(w in f.__name__.lower()
                                                                           for w in ("save", "write"))]
    loads = [f for f in functions_named("load_from_file", params=1) if any(w in f.__name__.lower()
                                                                             for w in ("load", "read"))]
    pairs = [_Pair(s, l) for s in saves for l in loads]
    return sorted(pairs, key=lambda p: (sum(not any(w in fn.__name__.lower() for w in _PREFER)
                                            for fn in (p.save, p.load)), p.__name__))


SAMPLES = [
    "Café résumé naïve Üntermensch",
    "東京 北京 서울 中文字符",
    "emoji: 😀🚀🎉 and 𝄞 music",
    "mixed: Ünïcödé 漢字 🐍 ascii",
    "",
    "line one\nline two ✓",
]


def test_round_trip(p):
    import os

    for i, text in enumerate(SAMPLES):
        path = os.path.abspath(f"hidden_test_roundtrip_{i}.txt")
        p.save(text, path)
        got = p.load(path)
        assert got == text, (text, got)


TESTS = [test_round_trip]
