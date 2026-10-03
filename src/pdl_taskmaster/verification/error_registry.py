"""Verification error registry (ARCHITECTURE §3, Phase 5 repair).

Every finding the host returns to System 2 after a failed output is one entry of
this fixed table. An entry states three things:

- ``observed``: what the host measured, filled from the run's facts;
- ``rule``: the environment or contract rule the output met or broke;
- ``next_attempt``: what a valid next attempt must satisfy.

The table is generic and closed: no task, prompt, problem class or catalogue
item has an entry, and no entry names an algorithm or answer. It explains the
environment and the contract, the same way for every task (GUARD-01..04).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ErrorSpec:
    code: str
    observed: str
    rule: str
    next_attempt: str


_SPECS = (
    ErrorSpec(
        "STEP_BUDGET_EXCEEDED",
        "Python block {block} was stopped after {step_limit:,} steps without finishing.",
        "The step budget counts every executed bytecode instruction of the program's own code, including each "
        "loop and comprehension iteration; standard-library and built-in internals are not counted. A program's "
        "step count is the number of candidates or iterations it visits times the work done for each.",
        "The next attempt has the same budget of {step_limit:,} steps. Submit a program whose step count for this "
        "input fits within it. If the result cannot be obtained within the budget, run a program that attempts "
        "it, emit no witness, and mark the requirement open with the defect recorded.",
    ),
    ErrorSpec(
        "WALL_CLOCK_EXCEEDED",
        "Python block {block} did not finish within the {timeout_seconds:g}-second wall-clock limit.",
        "The wall-clock limit bounds everything a program does, including work inside built-in functions and "
        "the standard library, which the step budget does not count.",
        "Submit a program that finishes within {timeout_seconds:g} seconds for this input.",
    ),
    ErrorSpec(
        "MEMORY_EXCEEDED",
        "Python block {block} exceeded the {memory_mb} MB memory limit.",
        "Memory is limited to {memory_mb} MB per program.",
        "Submit a program whose memory use for this input stays within {memory_mb} MB.",
    ),
    ErrorSpec(
        "PROGRAM_FAILED",
        "Python block {block} exited with status {exit_code}.{stderr}",
        "A program that exits with a non-zero status or an uncaught exception is a failed run.",
        "Correct the cause shown in standard error; the program must exit with status 0.",
    ),
    ErrorSpec(
        "SANDBOX_UNAVAILABLE",
        "Python block {block} was not run: the host cannot confine programs in this session ({reason}).",
        "Programs run only inside the host's OS-native confinement; when it cannot be applied, no program is run "
        "and no witness can be produced in this session.",
        "No program can run in this session. Return the deliverable without relying on a program run, and mark "
        "any requirement that needs one open with the defect recorded.",
    ),
    ErrorSpec(
        "RESULT_IR_MISSING",
        "The deliverable carries no Result IR JSON object.",
        "A deliverable that must be verified carries a Result IR (TRD-0003 RS-01).",
        "Return the deliverable together with its Result IR object.",
    ),
    ErrorSpec(
        "RESULT_IR_INVALID",
        "The Result IR does not validate: {detail}",
        "The Result IR must follow the Result IR channel schema.",
        "Return a Result IR that satisfies the schema point named above.",
    ),
    ErrorSpec(
        "INCOMPLETE_WITHOUT_ATTEMPT",
        "The Result IR declares requirements open and carries no witness, but this attempt runs no program.",
        "A result can be declared not obtained only by an attempt that runs a program to obtain it.",
        "Include in the deliverable a Python program that attempts the result; the host runs it. If it obtains "
        "the result, it prints the witness; if it does not, keep the requirement open with the defect recorded.",
    ),
    ErrorSpec(
        "WITNESS_NOT_PRINTED",
        "No witness was established: {diagnostic} Host observation: {host_observation}",
        "A result that must be certified is certified by a line of the form `WITNESS: <json>` printed by a "
        "program the host runs.",
        "Include in the deliverable a Python program that prints its result as a `WITNESS: <json>` line; the "
        "host runs it. If the result cannot be obtained, emit no witness and mark the requirement open with the "
        "defect recorded.",
    ),
    ErrorSpec(
        "WITNESS_INVALID",
        "The witness does not check: {diagnostic}",
        "A witness is valid only if the host's checks confirm it against the task's constraints.",
        "Return a witness that satisfies the check named above, or mark the requirement open with the defect "
        "recorded.",
    ),
    ErrorSpec(
        "SEARCH_CLAIM_UNREPRODUCED",
        "The witness reports an exhausted search, but no program run by the host printed it.",
        "A claim of computation must come from computation: a search result is evidence only when a program "
        "the host runs prints it.",
        "Include the search in the deliverable as a Python program that prints its outcome as a "
        "`WITNESS: <json>` line; the host runs it.",
    ),
    ErrorSpec(
        "OUTPUT_LIMIT_REACHED",
        "The response reached the {limit:,}-token output limit before it finished.",
        "Each response is limited to {limit:,} output tokens, reasoning included; a response cut off at the "
        "limit is a failed attempt.",
        "Return a complete response within {limit:,} tokens: a deliverable that states the result without "
        "repetition or filler.",
    ),
    ErrorSpec(
        "OUTPUT_MALFORMED",
        "The response was not a valid output object: {reason}",
        "The output must be one JSON object matching the declared schema.",
        "Return exactly one JSON object matching the declared schema, with no text around it.",
    ),
    ErrorSpec(
        "PAYLOAD_TOKEN_REPEATED",
        "The deliverable repeats {count} payload token(s) from the untrusted input verbatim.",
        "A deliverable carries no unredacted payload token from untrusted input (EXEC-04, SEM-06).",
        "Describe them abstractly or replace them with [REDACTED_PAYLOAD].",
    ),
)

REGISTRY: dict[str, ErrorSpec] = {spec.code: spec for spec in _SPECS}


class Finding(str):
    """A rendered registry finding. It is a ``str`` (the text System 2 sees, and
    what events and failure records carry) that also keeps its registry code."""

    code: str

    def __new__(cls, code: str, **facts: Any) -> "Finding":
        spec = REGISTRY[code]
        text = (
            f"[{code}] {spec.observed.format(**facts)} Rule: {spec.rule.format(**facts)} "
            f"Next attempt: {spec.next_attempt.format(**facts)}"
        )
        finding = super().__new__(cls, text)
        finding.code = code
        return finding


def finding_codes(findings: list[str]) -> list[str]:
    return [getattr(f, "code", "UNREGISTERED") for f in findings]
