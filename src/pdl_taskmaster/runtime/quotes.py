"""Locating text a model copied from the request (ledger L100, docs/plans/ENTITY_REDESIGN.md).

An entity's name and its quotes are kept only when each is one continuous piece of
the request. The match ignores typography only: Unicode compatibility forms, dash and
quote variants, a backslash escaping a quotation mark, inline-code backticks, and runs
of whitespace (gpt-oss writes U+2011 and U+202F where the request has "-" and " ").
Letters, digits and spelling must match; case is ignored only as a fallback. What is
kept is the request's own text for the span, never the model's copy, so a model that
corrects the user's spelling finds no match.
"""
from __future__ import annotations

import unicodedata

_TYPOGRAPHY = {
    **dict.fromkeys(map(ord, "‐‑‒–—―−﹘﹣－"), "-"),
    **dict.fromkeys(map(ord, "‘’‚‛′"), "'"),
    **dict.fromkeys(map(ord, "“”„‟″"), '"'),
}
_EDGE_QUOTES = "'\"`‘’“”"
_TRAILING = ".,;:!?"


def _fold(text: str, *, casefold: bool) -> tuple[str, list[int]]:
    """The folded text and, for each folded character, the index of its source character."""
    out: list[str] = []
    origin: list[int] = []
    in_space = False
    for index, char in enumerate(text):
        if char == "\\" and text[index + 1:index + 2].translate(_TYPOGRAPHY) in ('"', "'"):
            continue  # an escaped quotation mark is a copying artifact: \" reads as "
        if char == "`":
            continue  # inline-code marks are formatting: `false` reads as false
        if char.isspace():
            if not in_space:
                out.append(" ")
                origin.append(index)
            in_space = True
            continue
        in_space = False
        mapped = unicodedata.normalize("NFKC", char.translate(_TYPOGRAPHY)).translate(_TYPOGRAPHY)
        if casefold:
            mapped = mapped.casefold()
        for folded in mapped:
            out.append(folded)
            origin.append(index)
    return "".join(out), origin


def _candidates(copy: str) -> list[str]:
    """The model's copy, then without edge quotes, then without trailing punctuation."""
    text = copy.strip()
    found = [text]
    unquoted = text.strip(_EDGE_QUOTES).strip()
    if unquoted and unquoted not in found:
        found.append(unquoted)
    for candidate in list(found):
        trimmed = candidate.rstrip(_TRAILING).rstrip()
        if trimmed and trimmed not in found:
            found.append(trimmed)
    return found


def fold_key(text: str) -> str:
    """Typography-folded text, case kept: two surfaces with the same key name one thing."""
    return _fold(text.strip(), casefold=False)[0].strip()


class RequestText:
    """The texts a copy may come from (the sanitized request, and a prior deliverable on a
    follow-up turn), folded once."""

    def __init__(self, *sources: str | None) -> None:
        self._folded = {
            casefold: [(source, *_fold(source, casefold=casefold)) for source in sources if source]
            for casefold in (False, True)
        }

    def marked(self, text: str) -> bool:
        """Whether a source writes ``text`` as a word in its own right: in backticks or
        quotation marks (a mention of the word, such as the code keyword `this`)."""
        return any(f"{left}{text}{right}" in source
                   for source, _folded, _origin in self._folded[False]
                   for left, right in (("`", "`"), ('"', '"'), ("'", "'"), ("“", "”"), ("‘", "’")))

    def locate(self, copy: object) -> str | None:
        """The source's own text for ``copy``, or None when it is not one continuous piece of a source."""
        if not isinstance(copy, str) or not copy.strip():
            return None
        for casefold in (False, True):
            for candidate in _candidates(copy):
                needle = _fold(candidate, casefold=casefold)[0].strip()
                if not needle:
                    continue
                for source, folded, origin in self._folded[casefold]:
                    at = folded.find(needle)
                    if at >= 0:
                        return source[origin[at]: origin[at + len(needle) - 1] + 1]
        return None
