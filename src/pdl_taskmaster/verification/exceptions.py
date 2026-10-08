"""Typed Protocol Verification and Semantic Classification Exceptions."""

from __future__ import annotations


class ProtocolVerificationError(Exception):
    """Base class for host protocol verification exceptions."""


class PromptSemanticEvasionError(ProtocolVerificationError):
    """Raised when Prompt Pseudocode unpromptedly commands execution to evade or withhold deliverables."""

    def __init__(self, message: str, *, confidence: float | None = None, prompt_body: str = "") -> None:
        super().__init__(message)
        self.confidence = confidence
        self.prompt_body = prompt_body


class PlanSemanticEvasionError(ProtocolVerificationError):
    """Raised when Response Plan Pseudocode unpromptedly commands execution to evade or withhold deliverables."""

    def __init__(self, message: str, *, confidence: float | None = None, plan_body: str = "") -> None:
        super().__init__(message)
        self.confidence = confidence
        self.plan_body = plan_body
