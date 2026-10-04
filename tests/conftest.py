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
