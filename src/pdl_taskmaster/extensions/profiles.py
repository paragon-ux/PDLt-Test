"""Versioned compatibility profiles (L120 B2): how an extension point says what an extension must provide.

A profile names a kind and a version (``pdlt.task-type/1``), the required set of components, and the invariants the
whole declaration must satisfy. A declaration is a mapping of components plus ``profile``, the profile it targets.
Registration validates the declaration and refuses it with every problem named, by component; built-ins register
through the same call. A registered extension is built into a frozen object: what was validated is what runs.
"""
from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable, Generic, TypeVar

T = TypeVar("T")
# (component value, whole declaration, registry) -> problems; an empty list means the component conforms.
ComponentCheck = Callable[[Any, Mapping[str, Any], "Registry[Any]"], list[str]]
InvariantCheck = Callable[[Mapping[str, Any], "Registry[Any]"], list[str]]


@dataclass(frozen=True)
class Component:
    name: str
    description: str
    check: ComponentCheck


@dataclass(frozen=True)
class Invariant:
    name: str
    description: str
    check: InvariantCheck


@dataclass(frozen=True)
class Profile:
    kind: str
    version: int
    components: tuple[Component, ...]
    invariants: tuple[Invariant, ...] = ()

    @property
    def id(self) -> str:
        return f"pdlt.{self.kind}/{self.version}"

    def problems(self, declaration: Any, registry: "Registry[Any]") -> list[str]:
        """Every way ``declaration`` fails this profile, each naming its component or invariant. Invariants are
        checked only over a declaration whose components all conform."""
        if not isinstance(declaration, Mapping):
            return [f"declaration: a mapping of components is required, got {type(declaration).__name__}"]
        found: list[str] = []
        if declaration.get("profile") != self.id:
            found.append(f"profile: must be {self.id!r}, got {declaration.get('profile')!r}")
        for component in self.components:
            if component.name not in declaration:
                found.append(f"{component.name}: missing ({component.description})")
                continue
            try:
                found.extend(f"{component.name}: {p}" for p in component.check(declaration[component.name],
                                                                               declaration, registry))
            except Exception as exc:  # a check that cannot run is a non-conforming component, never a pass
                found.append(f"{component.name}: could not be checked ({type(exc).__name__}: {exc})")
        known = {c.name for c in self.components} | {"profile"}
        found.extend(f"{name}: not a component of {self.id}" for name in declaration if name not in known)
        if not found:
            for invariant in self.invariants:
                found.extend(f"invariant {invariant.name}: {p}" for p in invariant.check(declaration, registry))
        return found

    def describe(self) -> dict[str, Any]:
        return {"profile": self.id,
                "components": {c.name: c.description for c in self.components},
                "invariants": {i.name: i.description for i in self.invariants}}


class ProfileViolation(ValueError):
    """A declaration that does not conform to its profile. ``problems`` names each missing or invalid component."""

    def __init__(self, profile_id: str, name: Any, problems: list[str]):
        self.profile_id = profile_id
        self.name = name
        self.problems = list(problems)
        super().__init__(f"{name!r} does not conform to {profile_id}:\n" + "\n".join(f"- {p}" for p in problems))


class ExtensionFailure(RuntimeError):
    """An extension failed while the core used it. The core stops what it was doing; it never passes on a failure."""


class Registry(Generic[T]):
    """The extensions of one kind, in registration order. Every one, built-in or not, enters through register()."""

    def __init__(self, profile: Profile, *, key: str, build: Callable[[Mapping[str, Any]], T]):
        self.profile = profile
        self.key = key
        self._build = build
        self._items: dict[str, T] = {}

    def register(self, declaration: Mapping[str, Any], *, replace: bool = False) -> T:
        name = declaration.get(self.key) if isinstance(declaration, Mapping) else None
        problems = self.profile.problems(declaration, self)
        if not problems and name in self._items and not replace:
            problems = [f"{self.key}: {name!r} is already registered (pass replace=True to replace it)"]
        if problems:
            raise ProfileViolation(self.profile.id, name, problems)
        item = self._build(declaration)
        self._items[name] = item
        return item

    def get(self, name: str) -> T:
        if name not in self._items:
            raise KeyError(f"no {self.profile.kind} {name!r} is registered; registered: {', '.join(self._items)}")
        return self._items[name]

    def __contains__(self, name: object) -> bool:
        return name in self._items

    def names(self) -> list[str]:
        return list(self._items)

    def items(self) -> list[T]:
        return list(self._items.values())

    def _state(self) -> Any:
        return dict(self._items)

    def _restore(self, state: Any) -> None:
        self._items = state

    @contextmanager
    def scoped(self) -> Iterator["Registry[T]"]:
        """Registrations made inside are undone on exit (tests, and callers trying an extension)."""
        state = self._state()
        try:
            yield self
        finally:
            self._restore(state)


def unique_strings(value: Any, allowed: tuple[str, ...] | frozenset[str], *, non_empty: bool = False) -> list[str]:
    """Problems with a list of distinct strings drawn from ``allowed``."""
    if not isinstance(value, (list, tuple)) or not all(isinstance(v, str) for v in value):
        return [f"a list of strings drawn from {sorted(allowed)} is required, got {value!r}"]
    problems = [f"{v!r} is not one of {sorted(allowed)}" for v in value if v not in allowed]
    if len(set(value)) != len(value):
        problems.append("entries repeat")
    if non_empty and not value:
        problems.append("at least one entry is required")
    return problems
