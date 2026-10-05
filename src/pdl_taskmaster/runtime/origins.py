"""Origins of projection values (TARGET_ARCHITECTURE I-1, I-2, I-3).

Every value a model operation receives has exactly one origin:

* ``USER``: the user's own words (the request, a review message, supplied input),
  verbatim or sanitized by the host;
* ``HOST``: host-owned state and facts (standards, constraints, tools, protocol state);
* ``MODEL``: written by a model operation, named with the operations that may have
  produced it (``MODEL:DRAFT_PROMPT|REVISE_PROMPT``);
* ``PUBLISHED``: a previous turn's verified deliverable.

``EXECUTION_CONTRACT.json`` declares the origin of each symbol per operation; the
context compiler refuses a symbol with no declaration, and a ``Sourced`` value whose
origin differs from its declaration. The declarations are what the solver-isolation
test (I-3) reads.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Origin(str, Enum):
    USER = "USER"
    HOST = "HOST"
    MODEL = "MODEL"
    PUBLISHED = "PUBLISHED"


@dataclass(frozen=True)
class Declared:
    origin: Origin
    producers: tuple[str, ...] = ()

    @classmethod
    def parse(cls, text: str) -> "Declared":
        head, _, tail = str(text).partition(":")
        origin = Origin(head)
        producers = tuple(p for p in tail.split("|") if p)
        if (origin is Origin.MODEL) != bool(producers):
            raise ValueError(f"origin_declaration:{text}")  # MODEL names its producers; nothing else does
        return cls(origin, producers)

    def __str__(self) -> str:
        return self.origin.value + (":" + "|".join(self.producers) if self.producers else "")


class Sourced(str):
    """A string that carries its origin from where it was created. It behaves as the
    string itself (the projection serializes the same bytes); string operations on it
    return a plain ``str``, whose origin is then the declaration of the slot it fills."""

    origin: Origin
    producer: str | None

    def __new__(cls, value: str, origin: Origin, producer: str | None = None) -> "Sourced":
        if (origin is Origin.MODEL) != (producer is not None):
            raise ValueError("a MODEL value names its producing operation, and only a MODEL value does")
        instance = super().__new__(cls, value)
        instance.origin = origin
        instance.producer = producer
        return instance


class OriginMismatch(ValueError):
    pass


def check(symbol: str, value: object, declared: Declared) -> None:
    """Refuse a sourced value whose origin differs from the slot's declaration."""
    if not isinstance(value, Sourced):
        return
    if value.origin is not declared.origin or (
        value.origin is Origin.MODEL and value.producer not in declared.producers
    ):
        found = value.origin.value + (f":{value.producer}" if value.producer else "")
        raise OriginMismatch(f"origin_mismatch:{symbol}: declared {declared}, value from {found}")
