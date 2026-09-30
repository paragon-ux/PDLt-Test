"""Base Checker Protocol and Verification Verdict."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class ProblemDomain(str, Enum):
    """Typed domain selector for substantive verification.

    The harness registers no problem-specific checkers (GUARD-02): a witness may
    declare a ``domain``, and only a checker registered under that exact name is
    used. Everything else is checked structurally and reported provisional.
    """

    GENERAL = "general"

    @classmethod
    def from_string(cls, val: str | None) -> ProblemDomain | None:
        if not val:
            return None
        cleaned = val.strip().lower()
        for member in cls:
            if member.value == cleaned:
                return member
        return None


@dataclass(frozen=True)
class VerificationVerdict:
    """Outcome of mechanical substantive verification."""
    valid: bool
    diagnostic: Optional[str] = None
    provisional: bool = False
    details: Optional[dict[str, Any]] = None


class BaseChecker(ABC):
    """Abstract base class for all deterministic domain checkers (P2)."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique domain identifier for this checker."""
        ...

    @abstractmethod
    def check(
        self,
        witness: dict[str, Any] | Any,
        constraints: dict[str, Any],
        *,
        body: str | None = None,
    ) -> VerificationVerdict:
        """Deterministically verify whether the witness satisfies all mathematical/domain constraints."""
        ...
