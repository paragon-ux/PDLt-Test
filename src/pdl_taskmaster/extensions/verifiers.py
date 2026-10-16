"""Verifiers (verifier profile v1): domain checkers a task type binds by name.

A verifier judges a witness for its domain. It never establishes a result on its own: a result is host-verified
only when a program the host ran printed the witness (``reproduction: required``, the only value v1 allows), and the
level is computed by the host (runtime/provenance.py), never by the checker. The harness ships one verifier,
``witness-reproduction``: the structural check of any witness, domain ``general`` (ADR-0018: no problem-specific
checker ships in the harness plane).
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from pdl_taskmaster.extensions.profiles import Component, Invariant, Profile, Registry

PROFILE_ID = "pdlt.verifier/1"
NAME = re.compile(r"^[a-z][a-z0-9-]{1,63}$")
REPRODUCTION = ("required",)


@dataclass(frozen=True)
class Verifier:
    name: str
    domain: str
    checker: Any
    reproduction: str = "required"


def _name(value: Any, declaration: Mapping[str, Any], registry: Registry[Any]) -> list[str]:
    if not isinstance(value, str) or not NAME.match(value):
        return [f"lower-case letters, digits and hyphens, 2-64 characters, are required, got {value!r}"]
    return ["'none' is reserved: it is the binding of a task type with no verifier"] if value == "none" else []


def _domain(value: Any, declaration: Mapping[str, Any], registry: Registry[Any]) -> list[str]:
    if not isinstance(value, str) or not NAME.match(value):
        return [f"lower-case letters, digits and hyphens, 2-64 characters, are required, got {value!r}"]
    taken = [v.name for v in registry.items() if v.domain == value and v.name != declaration.get("name")]
    return [f"domain {value!r} is already answered by verifier {taken[0]!r}"] if taken else []


def _checker(value: Any, declaration: Mapping[str, Any], registry: Registry[Any]) -> list[str]:
    problems = []
    if not callable(getattr(value, "check", None)):
        problems.append("an object with check(witness, constraints, *, body=None) -> VerificationVerdict is required")
    if not isinstance(getattr(value, "name", None), str):
        problems.append("the checker needs a string name")
    return problems


def _reproduction(value: Any, declaration: Mapping[str, Any], registry: Registry[Any]) -> list[str]:
    return [] if value in REPRODUCTION else [
        f"must be one of {list(REPRODUCTION)}: a checker never establishes a result without the host reproducing "
        f"the witness; got {value!r}"]


PROFILE = Profile(
    kind="verifier",
    version=1,
    components=(
        Component("name", "the name task types bind", _name),
        Component("domain", "the problem domain whose witnesses it judges", _domain),
        Component("checker", "the deterministic checker (verification/checkers/base.py BaseChecker)", _checker),
        Component("reproduction", "'required': a result counts as host-verified only when a program the host ran "
                                  "printed the witness", _reproduction),
    ),
    invariants=(Invariant("deterministic", "the checker reads only the witness and the constraints it is given; "
                          "declared, and exercised by the conformance kit",
                          lambda declaration, registry: []),),
)

REGISTRY: Registry[Verifier] = Registry(PROFILE, key="name", build=lambda d: Verifier(
    name=d["name"], domain=d["domain"], checker=d["checker"], reproduction=d["reproduction"]))


def register_verifier(declaration: Mapping[str, Any], *, replace: bool = False) -> Verifier:
    return REGISTRY.register(declaration, replace=replace)


def output_verifier() -> Any:
    """A verifier registry for one session: every registered verifier's checker, under its domain."""
    from pdl_taskmaster.verification.output_verifier import OutputVerifier

    registry = OutputVerifier()
    for verifier in REGISTRY.items():
        registry.register(verifier.checker, domain=verifier.domain)
    return registry


def _builtin() -> None:
    from pdl_taskmaster.verification.checkers.fallback import FallbackChecker

    register_verifier({"profile": PROFILE_ID, "name": "witness-reproduction", "domain": "general",
                       "checker": FallbackChecker(), "reproduction": "required"})


_builtin()
