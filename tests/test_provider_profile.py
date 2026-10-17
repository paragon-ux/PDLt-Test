"""L124 D5: providers on the profile mechanism (provider profile v1), beside verifiers (verifier profile v1).
Registration names each problem; settings and the made object's interface are checked before use. Offline."""
from __future__ import annotations

import pytest

from pdl_taskmaster.extensions import providers, verifiers
from pdl_taskmaster.extensions.profiles import ExtensionFailure, ProfileViolation, Registry


def test_the_built_ins_are_registered_through_the_profile():
    assert providers.provider_names("worker") == ["api", "recorded"]
    assert providers.provider_names("system1") == ["openrouter"]
    assert all(isinstance(r, Registry) for r in (providers.REGISTRY, verifiers.REGISTRY))


def test_each_missing_or_invalid_component_is_named():
    with providers.REGISTRY.scoped(), pytest.raises(ProfileViolation) as caught:
        providers.register_provider({"profile": providers.PROFILE_ID, "name": "Bad Name", "role": "oracle",
                                     "settings": ["Model"]})
    problems = caught.value.problems
    for prefix in ("factory: missing", "name:", "role: must be one of", "settings:"):
        assert any(p.startswith(prefix) for p in problems), prefix


def test_an_unknown_setting_is_refused_before_the_factory_runs():
    made = []
    with providers.REGISTRY.scoped():
        providers.register_provider("listed", lambda **s: made.append(s), settings=["model"])
        with pytest.raises(ValueError, match=r"takes no setting \['temperature'\]; it takes \['model'\]"):
            providers.create_worker("listed", model="m", temperature=0.2)
    assert made == []


def test_what_a_factory_makes_is_checked_against_its_role():
    with providers.REGISTRY.scoped():
        providers.register_provider("hollow", lambda **s: object())
        with pytest.raises(ExtensionFailure, match="is not a worker .*no call"):
            providers.create_worker("hollow")


def test_system_1_is_a_provider_of_its_own():
    client = providers.create_system1("openrouter", api_key="k", model="lab/classifier")
    assert client.is_configured and client.model == "lab/classifier"
    with pytest.raises(ValueError, match="unknown provider 'openrouter'; known: api, recorded"):
        providers.create_worker("openrouter")
    with pytest.raises(ValueError, match="takes no setting"):
        providers.create_system1("openrouter", temperature=0.0)
