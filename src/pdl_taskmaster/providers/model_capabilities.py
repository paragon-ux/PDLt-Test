"""What a model supports, read from OpenRouter's model list before its first call (L122).

The API worker loads the selected model's metadata before adapting its output format, then checks
each outgoing round's actual parameters against ``supported_parameters``. An unsupported parameter
fails closed before that payload is sent, naming the model, parameter and operation. Cached metadata
does not authorize different later requirements. Only OpenRouter publishes this list; other endpoints
are not checked.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any

from pdl_taskmaster.providers.base import ATTRIBUTION_HEADERS

# The parameter, as OpenRouter names it in supported_parameters, that each output format needs.
FORMAT_PARAMETERS = {"schema": "structured_outputs", "json": "response_format"}

# What the person running PDLt can change when a parameter is missing.
REMEDIES = {
    "reasoning": "run without a reasoning setting (--api-reasoning-effort, --api-reasoning-operation)",
    "structured_outputs": "run with --no-structured-output, or choose a model that supports it",
    "response_format": "run with --no-structured-output, or choose a model that supports it",
    "tools": "run without --agent-tools",
}

_LISTS: dict[str, dict[str, dict[str, Any]]] = {}


def is_openrouter(base_url: str) -> bool:
    host = urllib.parse.urlsplit(base_url).hostname or ""
    return host == "openrouter.ai" or host.endswith(".openrouter.ai")


def model_list(base_url: str, timeout: float) -> dict[str, dict[str, Any]]:
    """OpenRouter's model list by model id, read once per process. A public list: no credentials are sent."""
    if base_url not in _LISTS:
        request = urllib.request.Request(f"{base_url}/models", headers=dict(ATTRIBUTION_HEADERS), method="GET")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read())
        _LISTS[base_url] = {str(m.get("id")): m for m in data.get("data") or [] if isinstance(m, dict)}
    return _LISTS[base_url]


def lookup(models: dict[str, dict[str, Any]], model_id: str) -> dict[str, Any] | None:
    """The model's entry. A routing shortcut (``:nitro``, ``:floor``) names the same model; a ``:free``
    variant is its own entry and never falls back to the paid one."""
    entry = models.get(model_id)
    if entry is None and ":" in model_id and not model_id.endswith(":free"):
        entry = models.get(model_id.split(":", 1)[0])
    return entry


def unsupported(entry: dict[str, Any], needs: dict[str, list[str]]) -> dict[str, list[str]]:
    """Each needed parameter the entry does not list, with the operations that send it."""
    supported = set(entry.get("supported_parameters") or [])
    return {parameter: operations for parameter, operations in needs.items() if parameter not in supported}


def describe(model: str, parameter: str, operations: list[str]) -> str:
    named = ", ".join(operations[:3]) + (f" and {len(operations) - 3} more" if len(operations) > 3 else "")
    return f"{model} does not support '{parameter}', which {named} would send; {REMEDIES.get(parameter, 'choose another model')}"
