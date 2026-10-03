"""Sys1 Backend Client Abstraction.

Implements decoupled invocation of Sys1 single-pass classification endpoints.
Defaults to configuring via SYS1_* environment variables.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any
import urllib.error
import urllib.request

from pdl_taskmaster.providers.sys1.schema import Sys1Request

logger = logging.getLogger(__name__)

DEFAULT_SYS1_ENDPOINT = "https://openrouter.ai/api/alpha/decisions"
DEFAULT_SYS1_MODEL = os.environ.get("SYS1_MODEL", "typesafe/jev-1.13")


class Sys1Client:
    """Client for invoking Sys1 non-generative classification backends."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        endpoint: str | None = None,
        model: str | None = None,
        timeout: float = 15.0,
    ) -> None:
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = (
                os.environ.get("SYS1_API_KEY")
                or os.environ.get("OPENROUTER_API_KEY")
                or ""
            )
        self.endpoint = (
            endpoint
            or os.environ.get("SYS1_ENDPOINT")
            or DEFAULT_SYS1_ENDPOINT
        )
        self.model = (
            model
            or os.environ.get("SYS1_MODEL")
            or DEFAULT_SYS1_MODEL
        )
        self.timeout = timeout

    @property
    def is_configured(self) -> bool:
        """Check whether the client has an API key configured."""
        return bool(self.api_key.strip())

    def call(self, request: Sys1Request) -> tuple[dict[str, Any], float]:
        """Invoke the Sys1 backend with the given request.

        Returns:
            Tuple of (response_body_dict, duration_ms).
        """
        if not self.is_configured:
            raise ValueError("Sys1 API key is not configured (set SYS1_API_KEY or OPENROUTER_API_KEY)")

        payload = request.to_dict()
        if "model" not in payload or not payload["model"]:
            payload["model"] = self.model

        req_data = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "PDL-Taskmaster/Sys1Client",
        }

        req = urllib.request.Request(
            self.endpoint,
            data=req_data,
            headers=headers,
            method="POST",
        )

        # Call lifecycle (providers/call_trace.py), recorded by the owning worker when it has one.
        from contextlib import nullcontext

        from pdl_taskmaster.providers.call_trace import tracking

        tracer = getattr(self, "tracer", None)
        trace = tracer.begin_call("SYSTEM1:" + next(iter(request.questions), "decision")) if tracer else None
        attempt = trace.new_attempt(req_data) if trace else None
        t0 = time.perf_counter()
        try:
            with tracking(attempt) if attempt else nullcontext():
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    elapsed_ms = (time.perf_counter() - t0) * 1000.0
                    if attempt:
                        attempt.mark("acknowledged")
                        attempt.status = getattr(resp, "status", None)
                    raw = resp.read()
            if attempt:
                attempt.mark("response_started")
                attempt.mark("response_complete")
                attempt.response_bytes, attempt.outcome = len(raw), "completed"
                trace.final = "completed"
            return json.loads(raw.decode("utf-8")), elapsed_ms
        except KeyboardInterrupt:
            if attempt:
                attempt.outcome, attempt.interrupted_by, trace.final = "interrupted", "local", "interrupted"
            raise
        except urllib.error.HTTPError as e:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            if attempt:
                attempt.mark("acknowledged")
                attempt.status, attempt.outcome, trace.final = e.code, "http_error", "failed"
            err_body = e.read().decode("utf-8", errors="replace")
            logger.warning("Sys1 backend returned HTTP %d: %s", e.code, err_body)
            raise RuntimeError(f"Sys1 HTTP {e.code}: {err_body}") from e
        except Exception as e:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            if attempt:
                attempt.outcome, attempt.error, trace.final = "transport_error", f"{type(e).__name__}: {e}", "failed"
            logger.warning("Sys1 backend request failed after %.1fms: %s", elapsed_ms, e)
            raise
        finally:
            if tracer:
                tracer.end_call(trace)
