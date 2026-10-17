"""Model providers (provider profile v1, ``pdlt.provider/1``; L124 D5).

A provider is a named factory for one role:
- ``worker``: the model that runs the operations; it returns an object with ``call(request) -> WorkerResult``.
- ``system1``: the classifier System 1 asks; it returns an object with ``is_configured`` and
  ``call(request) -> (answer, milliseconds)``.

A provider declares the settings its factory takes ("any", or their names). Unknown settings are refused before the
factory runs, and every object a factory returns is checked against its role's interface before anything uses it.
Built in: ``api`` and ``recorded`` (workers) and ``openrouter`` (System 1), registered through the same call.
"""
from __future__ import annotations

import inspect
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pdl_taskmaster.extensions.profiles import Component, ExtensionFailure, Profile, Registry

PROFILE_ID = "pdlt.provider/1"
NAME = re.compile(r"^[a-z][a-z0-9-]{1,63}$")
ROLES = {"worker": "call(request) -> WorkerResult",
         "system1": "is_configured, and call(request) -> (answer, milliseconds)"}
IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]*$")


@dataclass(frozen=True)
class Provider:
    name: str
    role: str
    factory: Callable[..., Any]
    settings: frozenset[str] | None  # None: any keyword


def _name(value: Any, declaration: Mapping[str, Any], registry: Registry[Any]) -> list[str]:
    return [] if isinstance(value, str) and NAME.match(value) else [
        f"lower-case letters, digits and hyphens, 2-64 characters, are required, got {value!r}"]


def _role(value: Any, declaration: Mapping[str, Any], registry: Registry[Any]) -> list[str]:
    return [] if value in ROLES else [f"must be one of {sorted(ROLES)}, got {value!r}"]


def _factory(value: Any, declaration: Mapping[str, Any], registry: Registry[Any]) -> list[str]:
    return [] if callable(value) else ["a callable taking the provider's settings as keywords is required"]


def _settings(value: Any, declaration: Mapping[str, Any], registry: Registry[Any]) -> list[str]:
    if value == "any":
        return []
    if not isinstance(value, (list, tuple)) or not all(isinstance(v, str) and IDENTIFIER.match(v) for v in value):
        return [f"'any' or a list of lower-case setting names is required, got {value!r}"]
    return ["entries repeat"] if len(set(value)) != len(value) else []


PROFILE = Profile(
    kind="provider",
    version=1,
    components=(
        Component("name", "the name a run selects it by", _name),
        Component("role", f"what it provides: {', '.join(f'{k} ({v})' for k, v in ROLES.items())}", _role),
        Component("factory", "makes one instance from the settings", _factory),
        Component("settings", "'any', or the setting names the factory takes", _settings),
    ),
)

REGISTRY: Registry[Provider] = Registry(PROFILE, key="name", build=lambda d: Provider(
    name=d["name"], role=d["role"], factory=d["factory"],
    settings=None if d["settings"] == "any" else frozenset(d["settings"])))


def register_provider(name: str | Mapping[str, Any], factory: Callable[..., Any] | None = None, *,
                      role: str = "worker", settings: Any = "any", replace: bool = False) -> Provider:
    """Register a provider from a declaration, or from a name and a factory (role and settings as given)."""
    declaration = name if isinstance(name, Mapping) else {
        "profile": PROFILE_ID, "name": name, "role": role, "factory": factory, "settings": settings}
    return REGISTRY.register(declaration, replace=replace)


def provider_names(role: str = "worker") -> list[str]:
    return sorted(p.name for p in REGISTRY.items() if p.role == role)


def interface_problems(role: str, made: Any) -> list[str]:
    problems = [] if callable(getattr(made, "call", None)) else ["it has no call()"]
    if role == "system1" and not hasattr(made, "is_configured"):
        problems.append("it has no is_configured")
    return problems


def create(name: str, *, role: str = "worker", **settings: Any) -> Any:
    """An instance from provider ``name`` of ``role``. An unknown name or setting is refused before the factory
    runs; an instance that does not implement the role's interface is refused before anything uses it."""
    if name not in REGISTRY or REGISTRY.get(name).role != role:
        raise ValueError(f"unknown provider {name!r}; known: {', '.join(provider_names(role))}")
    provider = REGISTRY.get(name)
    if provider.settings is not None and set(settings) - provider.settings:
        raise ValueError(f"provider {name!r} takes no setting {sorted(set(settings) - provider.settings)}; "
                         f"it takes {sorted(provider.settings)}")
    made = provider.factory(**settings)
    problems = interface_problems(role, made)
    if problems:
        raise ExtensionFailure(f"provider {name!r} made a {type(made).__name__}, which is not a {role} "
                               f"({ROLES[role]}): {'; '.join(problems)}")
    return made


def create_worker(name: str, **settings: Any) -> Any:
    return create(name, role="worker", **settings)


def create_system1(name: str, **settings: Any) -> Any:
    return create(name, role="system1", **settings)


# ---- the built-ins, through the same path ---------------------------------------------------------------------

def _keywords(cls: type) -> list[str]:
    return [p.name for p in inspect.signature(cls.__init__).parameters.values()
            if p.kind is inspect.Parameter.KEYWORD_ONLY]


def _api(**settings: Any) -> Any:
    from pdl_taskmaster.api.session import default_repo_root
    from pdl_taskmaster.providers.api_worker import ApiWorker

    settings.setdefault("repo_root", default_repo_root())  # as Session.open defaults it
    return ApiWorker(**settings)


def _recorded(*, repo_root: str | Path, evidence: str | Path, eval_root: str | Path | None = None,
              case_ids: list[str] | None = None) -> Any:
    from pdl_taskmaster.providers.fixtures import build_recorded_fixture, build_recorded_fixture_from_vendored

    evidence = Path(evidence)
    if evidence.name == "recorded-cases.json":
        return build_recorded_fixture_from_vendored(repo_root, evidence, case_ids=case_ids)
    if eval_root is None:
        raise ValueError("eval_root is required for recorded evidence other than recorded-cases.json")
    return build_recorded_fixture(repo_root, Path(eval_root), evidence, case_ids=case_ids)


def _openrouter(**settings: Any) -> Any:
    from pdl_taskmaster.providers.sys1.client import Sys1Client

    return Sys1Client(**settings)


def _builtin() -> None:
    from pdl_taskmaster.providers.api_worker import ApiWorker
    from pdl_taskmaster.providers.sys1.client import Sys1Client

    register_provider({"profile": PROFILE_ID, "name": "api", "role": "worker", "factory": _api,
                       "settings": _keywords(ApiWorker)})
    register_provider({"profile": PROFILE_ID, "name": "recorded", "role": "worker", "factory": _recorded,
                       "settings": ["repo_root", "evidence", "eval_root", "case_ids"]})
    register_provider({"profile": PROFILE_ID, "name": "openrouter", "role": "system1", "factory": _openrouter,
                       "settings": _keywords(Sys1Client)})


_builtin()
