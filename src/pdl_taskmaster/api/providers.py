"""Model providers by name (L120 extension point), on provider profile v1 (extensions/providers.py, L124 D5). The
REPL, headless runs and library callers create workers here, never by naming a class.

Built in: ``api`` (the OpenAI-compatible Responses API worker; settings are ApiWorker's keywords) and ``recorded``
(replays recorded model outputs: ``repo_root``, ``evidence``, ``eval_root``, ``case_ids``) as workers; ``openrouter``
(Sys1Client) as System 1.
"""
from pdl_taskmaster.extensions.providers import (REGISTRY, create, create_system1, create_worker, provider_names,
                                                 register_provider)

__all__ = ["REGISTRY", "create", "create_system1", "create_worker", "provider_names", "register_provider"]
