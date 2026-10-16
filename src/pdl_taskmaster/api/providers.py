"""Model providers by name (L120 extension point). A provider is a factory that returns a worker: any object with
``call(request) -> WorkerResult`` (``providers.base.WorkerAdapter``). The REPL, headless runs and library callers
create workers here, never by naming a class.

Built in:
- ``api``: the OpenAI-compatible Responses API worker (OpenRouter by default); settings are ApiWorker's keywords.
- ``recorded``: replays recorded model outputs; ``evidence`` is a ``recorded-cases.json`` fixture, or recorded
  evidence with its ``eval_root``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

Factory = Callable[..., Any]
_FACTORIES: dict[str, Factory] = {}


def register_provider(name: str, factory: Factory, *, replace: bool = False) -> None:
    """Make ``factory(**settings)`` available as provider ``name``."""
    if name in _FACTORIES and not replace:
        raise ValueError(f"provider {name!r} is already registered")
    _FACTORIES[name] = factory


def provider_names() -> list[str]:
    return sorted(_FACTORIES)


def create_worker(name: str, **settings: Any) -> Any:
    """A worker from provider ``name`` with ``settings``. An unknown name is an error naming the known ones."""
    if name not in _FACTORIES:
        raise ValueError(f"unknown provider {name!r}; known: {', '.join(provider_names())}")
    return _FACTORIES[name](**settings)


def _api(**settings: Any) -> Any:
    from pdl_taskmaster.providers.api_worker import ApiWorker

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


register_provider("api", _api)
register_provider("recorded", _recorded)
