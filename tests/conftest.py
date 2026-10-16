"""The offline suite never reaches a live model: credentials are stripped for every test."""
from __future__ import annotations

import pytest

_CREDENTIAL_VARS = ("OPENROUTER_API_KEY", "SYS1_API_KEY", "SYS1_ENDPOINT")


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    for name in _CREDENTIAL_VARS:
        monkeypatch.delenv(name, raising=False)
    # On Windows the API worker otherwise reads the key from the Machine/User registry.
    from pdl_taskmaster.providers.api_worker import ApiWorker

    monkeypatch.setattr(ApiWorker, "_default_api_key_command", staticmethod(lambda env_name: None))
    # OpenRouter's model list is not fetched either: every model supports every parameter unless a test
    # supplies its own list (L122, tests/test_l122_provider_compat.py).
    from pdl_taskmaster.providers import model_capabilities

    monkeypatch.setattr(model_capabilities, "model_list", lambda base_url, timeout: _EveryModel())


class _EveryModel(dict):
    def get(self, key, default=None):
        return {"id": key, "supported_parameters": ["reasoning", "response_format", "structured_outputs", "tools"]}
