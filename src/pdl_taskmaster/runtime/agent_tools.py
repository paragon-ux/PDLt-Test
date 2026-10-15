"""In-call agent tools (ADR-0029): inside one model call, the worker may inspect before it commits, and its reply
is a validated submission. Off by default (``--agent-tools``); measured in ledger L111/L112.

The registry gives each operation its tools:
  EXECUTE_UNCONFIRMED   read_attempt (the previous attempt's programs as the host ran them, numbered, with the
                        correction; only when there is a previous attempt), run_python (a run in the session's confined
                        sandbox at the attempt's limits) and submit_execute_unconfirmed;
  BOOTSTRAP_ANALYSIS    submit_bootstrap_analysis (checked by the wire model);
  DRAFT_PROMPT          submit_draft_prompt (the wire model, then the host's pseudocode notation lint);
  DRAFT_PLAN            submit_draft_plan (the same).
Every submission is checked by the host's own post-call checks before it is accepted, and only those.

Integrity invariants, enforced here and not by the model:
  1. no tool returns a referee verdict: the submission check is structural (the wire model, the programs run as
     the host will run them, a WITNESS line printed when one is required); the host verifies the accepted reply
     itself afterwards, in its own sandbox run;
  2. tool output is never evidence and never reaches the deliverable or the protocol state;
  3. every run is a normal sandbox run at the attempt's limits; tool calls and submissions are budgeted;
  4. every tool call and submission is recorded (``on_record``, an AGENT_TOOL_CALL event);
  5. descriptions state capabilities and facts, never methods (GUARD-01, ADR-0025 section 6).

Provider fact: Cerebras rejects ``tools`` together with ``response_format``. Tool turns carry no output format; the
submission carries the operation's output schema in its parameters.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable

MAX_TOOL_CALLS = 6        # read_attempt and run_python, per model call
MAX_SUBMISSIONS = 3
OUTPUT_CHARS = 2000
SUBMIT = "submit_execute_unconfirmed"
WORK_TOOLS = ("read_attempt", "run_python")
SUBMITS = {"EXECUTE_UNCONFIRMED": SUBMIT, "BOOTSTRAP_ANALYSIS": "submit_bootstrap_analysis",
           "DRAFT_PROMPT": "submit_draft_prompt", "DRAFT_PLAN": "submit_draft_plan"}
TOOL_OPERATIONS = tuple(SUBMITS)  # the registry: operations whose calls may carry tools
SUBMIT_ONLY_OPERATIONS = ("BOOTSTRAP_ANALYSIS", "DRAFT_PROMPT", "DRAFT_PLAN")
_SCHEMA_SUBMIT_DESCRIPTION = (
    "Submit this call's outcome: the object the output_schema in the input declares. The host checks it against that "
    "schema. If the outcome cannot be accepted, the result lists each error with where it is, what was found and what "
    "is required, and you may submit again (at most 3 submissions). An accepted outcome ends the call.")
_DRAFT_SUBMIT_DESCRIPTION = (
    "Submit this call's outcome: the object the output_schema in the input declares. The host checks it against that "
    "schema and applies its pseudocode notation lint to the body (the same lint it applies after the call). If the "
    "outcome cannot be accepted, the result lists each error with where it is, what was found and what is required, "
    "and you may submit again (at most 3 submissions). An accepted outcome ends the call.")
_OUTCOME_SCHEMA = {"type": "object", "properties": {"outcome": {"type": "object"}}, "required": ["outcome"],
                   "additionalProperties": False}

TOOLS = [
    {"name": "read_attempt",
     "description": ("The previous attempt's program exactly as the host ran it, with line numbers, and the "
                     "host's correction for that attempt."),
     "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "run_python",
     "description": ("Run a Python program in the host sandbox under the same limits as the deliverable "
                     "(see AVAILABLE_EXECUTION_TOOLS). Returns the exit status, standard output and standard "
                     "error (each up to the last 2,000 characters), the steps used, and whether the step "
                     "budget stopped it. A run here is for your own inspection and is not evidence."),
     "inputSchema": {"type": "object", "properties": {"code": {"type": "string", "description": "Python source"}},
                     "required": ["code"], "additionalProperties": False}},
    {"name": SUBMIT,
     "description": ("Submit this call's outcome: the object the output_schema in the input declares. The host "
                     "checks it against that schema and runs the deliverable's programs as it will run them "
                     "(the whole body when it is a Python program, otherwise each ```python block). If the "
                     "outcome cannot be accepted, the result lists each error with what was found and what is "
                     "required, and you may submit again (at most 3 submissions). An accepted outcome ends the "
                     "call; the host then verifies the deliverable itself."),
     "inputSchema": _OUTCOME_SCHEMA},
    {"name": "submit_bootstrap_analysis", "description": _SCHEMA_SUBMIT_DESCRIPTION, "inputSchema": _OUTCOME_SCHEMA},
    {"name": "submit_draft_prompt", "description": _DRAFT_SUBMIT_DESCRIPTION, "inputSchema": _OUTCOME_SCHEMA},
    {"name": "submit_draft_plan", "description": _DRAFT_SUBMIT_DESCRIPTION, "inputSchema": _OUTCOME_SCHEMA},
]

Validator = Callable[[dict[str, Any]], tuple[list[dict[str, Any]], list[str]]]


def _phrase(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def responses_tools(names: list[str], outcome_schema: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """The named MCP-shaped definitions as Responses API function tools; the submission carries the call's own
    output schema when given (the schema the projection shows)."""
    tools = []
    for t in TOOLS:
        if t["name"] not in names:
            continue
        params = t["inputSchema"]
        if t["name"] in SUBMITS.values() and outcome_schema is not None:
            params = {**params, "properties": {"outcome": outcome_schema}}
        tools.append({"type": "function", "name": t["name"], "description": t["description"], "parameters": params})
    return tools


@dataclass
class ToolHost:
    """Runs one model call's tools. ``sandbox`` is the session's confined sandbox (unused by a submit-only operation);
    ``validate`` is the host's submission check: (errors, facts) for an outcome; ``on_record`` receives every tool
    call and submission."""

    sandbox: Any
    step_limit: int
    timeout: float
    memory_limit: int
    attempt_programs: list[str]
    correction: str
    validate: Validator
    attempt: int = 1
    on_record: Callable[[dict[str, Any]], None] | None = None
    operation: str = "EXECUTE_UNCONFIRMED"
    calls: list[dict[str, Any]] = field(default_factory=list)
    submissions: list[dict[str, Any]] = field(default_factory=list)

    @property
    def submit_name(self) -> str:
        return SUBMITS[self.operation]

    def tool_names(self) -> list[str]:
        """The tools this call exposes: on EXECUTE_UNCONFIRMED, read_attempt only when there is a previous attempt;
        a submit-only operation exposes only its submission."""
        if self.operation in SUBMIT_ONLY_OPERATIONS:
            return [self.submit_name]
        return (["read_attempt"] if (self.attempt_programs or self.correction) else []) + ["run_python", SUBMIT]

    def capability_note(self) -> str:
        names = self.tool_names()
        if self.operation in SUBMIT_ONLY_OPERATIONS:
            return (f"TOOLS FOR THIS CALL: {self.submit_name} (see its description). Answer by calling "
                    f"{self.submit_name} with the outcome. At most {MAX_SUBMISSIONS} submissions.")
        work = [n for n in names if n in WORK_TOOLS]
        return (f"TOOLS FOR THIS CALL: {_phrase(names)} (see their descriptions). Answer by calling {SUBMIT} with "
                f"the outcome. At most {MAX_TOOL_CALLS} calls of {_phrase(work)}, and {MAX_SUBMISSIONS} submissions. "
                "Tool results are for your inspection only.")

    def work_calls(self) -> int:
        return sum(c["tool"] in WORK_TOOLS for c in self.calls)

    def read_attempt(self) -> str:
        parts = []
        for index, program in enumerate(self.attempt_programs, 1):
            numbered = "\n".join(f"{n:4d}  {line}" for n, line in enumerate(program.splitlines(), 1))
            parts.append(f"Python block {index} (program.py):\n{numbered}")
        if not parts:
            parts.append("The previous attempt contained no program the host ran.")
        return "\n\n".join(parts) + "\n\n" + (self.correction or "")

    def run_python(self, code: str) -> str:
        run = self.sandbox.run_code(code, timeout=self.timeout, memory_limit=self.memory_limit,
                                    step_limit=self.step_limit)
        stdout = (run.stdout or "")[-OUTPUT_CHARS:]
        stderr = (run.stderr or "")[-OUTPUT_CHARS:]
        return (f"exit status: {run.exit_code}\nsteps used: {run.steps_used}\n"
                f"step budget exceeded: {bool(run.step_budget_exceeded)}\ntimed out: {bool(run.timed_out)}\n"
                f"standard output:\n{stdout}\nstandard error:\n{stderr}")

    def _record(self, record: dict[str, Any]) -> None:
        if self.on_record is not None:
            self.on_record(record)

    def dispatch(self, name: str, arguments: str) -> str:
        started = time.perf_counter()
        try:
            args = json.loads(arguments or "{}")
            if not isinstance(args, dict):
                raise ValueError("arguments are not an object")
            if name not in self.tool_names() or name in SUBMITS.values():
                output = f"error: no tool named {name!r}; the tools are {_phrase(self.tool_names())}"
            elif name == "read_attempt":
                output = self.read_attempt()
            elif isinstance(args.get("code"), str):
                output = self.run_python(args["code"])
            else:
                output = "error: run_python needs a string argument 'code'"
        except ValueError as exc:
            output = f"error: the arguments are not valid JSON ({exc})"
        record = {"n": len(self.calls) + 1, "attempt": self.attempt, "tool": name, "arguments": arguments,
                  "output": output, "ms": round((time.perf_counter() - started) * 1000, 1)}
        self.calls.append(record)
        self._record(record)
        return output

    def submit(self, arguments: str) -> tuple[dict[str, Any], dict[str, Any] | None]:
        """One submission: (the result envelope, the outcome when accepted)."""
        started = time.perf_counter()
        outcome: Any = None
        try:
            outcome = _unwrap_outcome(json.loads(arguments or "{}"))
        except ValueError as exc:
            errors, facts = [{"code": "OUTPUT_MALFORMED", "path": "arguments", "problem": f"not valid JSON ({exc})",
                              "expected": "an object with the field outcome"}], []
        else:
            if not isinstance(outcome, dict):
                errors, facts = [{"code": "OUTPUT_MALFORMED", "path": "outcome", "problem": "missing or not an object",
                                  "expected": "the object the output_schema declares"}], []
            else:
                errors, facts = self.validate(outcome)
        accepted = not errors
        envelope = {"ok": True, "result": "accepted; the host now verifies the deliverable", "facts": facts} if accepted \
            else {"ok": False, "errors": errors, "facts": facts,
                  "submissions_left": MAX_SUBMISSIONS - len(self.submissions) - 1}
        record = {"n": len(self.submissions) + 1, "attempt": self.attempt, "tool": self.submit_name,
                  "operation": self.operation, "accepted": accepted, "envelope": envelope, "outcome": outcome,
                  "ms": round((time.perf_counter() - started) * 1000, 1)}
        self.submissions.append(record)
        self._record(record)
        return envelope, (outcome if accepted else None)


def _unwrap_outcome(args: Any) -> Any:
    """Alias coercion (ADR-0018) for the submission's one argument: an outcome sent without the ``outcome`` wrapper,
    or wrapped twice, is the outcome itself."""
    if not isinstance(args, dict):
        return None
    outcome = args.get("outcome", args if args else None)
    while isinstance(outcome, dict) and set(outcome) == {"outcome"} and isinstance(outcome["outcome"], dict):
        outcome = outcome["outcome"]
    return outcome


def _message_text(data: dict[str, Any]) -> str:
    return "".join(part.get("text", "") for item in data.get("output") or [] if item.get("type") == "message"
                   for part in item.get("content") or [] if part.get("type") == "output_text").strip()


def _json_object(text: str) -> dict[str, Any] | None:
    try:
        value = json.JSONDecoder().raw_decode(text[text.index("{"):])[0]
    except (ValueError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def run_loop(body: dict[str, Any], send: Callable[[dict[str, Any]], dict[str, Any]], host: ToolHost,
             outcome_schema: dict[str, Any] | None = None) -> tuple[str, dict[str, Any]]:
    """The body the worker built, run as a tool loop that ends in an accepted submission. Returns (reply text,
    summary).

    Tool turns carry the tools and no output format. A plain JSON message is taken as a submission. When the
    budgets are spent, the last submission the wire model accepted stands as the reply (the host verifies and
    corrects it as any reply); otherwise one last call goes without tools and with the body's own format."""
    output_format = body.get("text")
    items: list[dict[str, Any]] = [{"type": "message", "role": "user", "content": body["input"]}]
    base = {k: v for k, v in body.items() if k not in ("text", "input")}
    base["instructions"] = (body.get("instructions") or "") + "\n\n" + host.capability_note()
    usage = {"input_tokens": 0, "output_tokens": 0}
    state = {"turns": 0, "schema": outcome_schema, "schema_fallback": False}

    def summary(final: str) -> dict[str, Any]:
        return {"tool_calls": len(host.calls), "submissions": len(host.submissions), "turns": state["turns"],
                "final": final, "usage": dict(usage), "schema_fallback": state["schema_fallback"]}

    def call(request: dict[str, Any]) -> dict[str, Any]:
        state["turns"] += 1
        data = send(request)
        for key in usage:
            usage[key] += int((data.get("usage") or {}).get(key) or 0)
        return data

    def tool_turn() -> dict[str, Any]:
        try:
            return call({**base, "input": items, "tools": responses_tools(host.tool_names(), state["schema"]),
                         "tool_choice": "auto"})
        except Exception:
            if state["schema"] is None:
                raise
            state["schema"], state["schema_fallback"] = None, True  # the provider refused the full schema
            return call({**base, "input": items, "tools": responses_tools(host.tool_names(), None),
                         "tool_choice": "auto"})

    while len(host.submissions) < MAX_SUBMISSIONS:
        data = tool_turn()
        function_calls = [o for o in data.get("output") or [] if o.get("type") == "function_call"]
        if not function_calls:
            outcome = _json_object(_message_text(data))
            if outcome is None:
                break
            envelope, accepted = host.submit(json.dumps({"outcome": outcome}))
            if accepted is not None:
                return json.dumps(accepted, ensure_ascii=False), summary("message")
            items += [o for o in data.get("output") or [] if o.get("type") == "message"]
            items.append({"type": "message", "role": "user",
                          "content": f"{host.submit_name} result: {json.dumps(envelope)}"})
            continue
        items += data.get("output") or []
        for fc in function_calls:
            name, cid = fc.get("name", ""), fc.get("call_id")
            if name == host.submit_name:
                if len(host.submissions) >= MAX_SUBMISSIONS:
                    output = "error: the submission budget is spent"
                else:
                    envelope, accepted = host.submit(fc.get("arguments", ""))
                    if accepted is not None:
                        return json.dumps(accepted, ensure_ascii=False), summary("submitted")
                    output = json.dumps(envelope, ensure_ascii=False)
            elif name in WORK_TOOLS and host.work_calls() >= MAX_TOOL_CALLS:
                output = "error: the tool-call budget is spent; submit now"
            else:
                output = host.dispatch(name, fc.get("arguments", ""))
            items.append({"type": "function_call_output", "call_id": cid, "output": output})
        if state["turns"] > MAX_TOOL_CALLS + MAX_SUBMISSIONS + 2:
            break
    last = next((s["outcome"] for s in reversed(host.submissions) if isinstance(s.get("outcome"), dict)
                 and not any(e.get("code") == "OUTPUT_MALFORMED" for e in (s.get("envelope") or {}).get("errors", []))),
                None)
    if last is not None:
        return json.dumps(last, ensure_ascii=False), summary("last-submission")
    final = {**base, "input": items}
    if output_format:
        final["text"] = output_format
    data = call(final)
    return _message_text(data), summary("formatted")


def make_validator(bridge: Any, sandbox: Any, budget: Any, witness_required: bool,
                   python_blocks: Callable[[str], list[str]], parse_witness: Callable[[str], Any]) -> Validator:
    """The host's existing checks, run before an outcome is accepted: the wire model (the operation bridge's parse,
    Pydantic), then the deliverable's programs run as the host runs them (``python_blocks``). Structural facts only;
    the witness itself is checked by the host's verification afterwards."""

    def validate(outcome: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
        try:
            parsed = bridge.parse_unconfirmed_execution(json.dumps(outcome))
        except Exception as exc:
            return [{"code": "OUTPUT_MALFORMED", "path": "outcome", "problem": str(exc)[:1200],
                     "expected": "an object matching the output_schema in the input"}], []
        if parsed.kind != "RESULT":
            return [], []
        from pdl_taskmaster.runtime.witness_forms import argued_result, declared_certificate, with_certificate

        open_defects = bool((parsed.result_ir or {}).get("open_defects"))
        argued = argued_result((parsed.result_ir or {}).get("witness"))  # L119: no program required
        certificate = declared_certificate(parsed.result_ir) if witness_required else None
        blocks = python_blocks(parsed.body)
        errors: list[dict[str, Any]] = []
        facts: list[str] = []
        printed = False
        if not blocks and witness_required and not open_defects and not argued:
            errors.append({"code": "NO_PROGRAM", "path": "outcome.body",
                           "problem": "the host would run no program from body: it is not a Python program and "
                                      "has no ```python block",
                           "expected": "a program in body that prints the WITNESS line"})
        for index, block in enumerate(blocks, 1):
            run = sandbox.run_code(with_certificate(block, certificate), timeout=budget.timeout_seconds,
                                   memory_limit=budget.memory_limit_bytes, step_limit=budget.step_limit)
            parsed_witness = parse_witness(run.stdout or "") if run.success else None
            witness = parsed_witness is not None
            printed |= witness
            facts.append(f"python block {index}: exit status {run.exit_code}, steps used {run.steps_used}, "
                         f"step budget exceeded {bool(run.step_budget_exceeded)}, printed a WITNESS line {witness}")
            if isinstance(parsed_witness, dict) and parsed_witness.get("polarity") == "negative":
                # L110: a fact about the host, not a rejection
                facts.append(f"python block {index} printed a negative WITNESS line: the host cannot check that no "
                             "result exists, so it publishes a negative result as unverified")
            if run.step_budget_exceeded and not open_defects:
                errors.append({"code": "STEP_BUDGET_EXCEEDED", "path": f"outcome.body block {index}",
                               "problem": f"stopped after {budget.step_limit:,} steps without finishing",
                               "expected": "a program that finishes within the step budget, or the requirement "
                                           "declared open in result_ir.open_defects"})
            elif not run.success and not run.step_budget_exceeded:
                errors.append({"code": "PROGRAM_FAILED", "path": f"outcome.body block {index}",
                               "problem": f"exit status {run.exit_code}; standard error: {(run.stderr or '')[-1200:]}",
                               "expected": "exit status 0"})
        if witness_required and blocks and not printed and not open_defects and not errors and not argued:
            errors.append({"code": "WITNESS_NOT_PRINTED", "path": "outcome.body",
                           "problem": "the programs ran, and none printed a line starting with 'WITNESS: '",
                           "expected": "a program that prints the WITNESS line, or the requirement declared open "
                                       "in result_ir.open_defects"})
        return errors, facts

    return validate


def _wire_errors(exc: Exception) -> list[dict[str, Any]]:
    """Every error of one failed wire parse, one envelope entry each (the Pydantic errors when there are any)."""
    validation = getattr(exc, "validation_error", None)
    entries = validation.errors() if validation is not None and hasattr(validation, "errors") else []
    errors = []
    for e in entries[:20]:
        path = ".".join(str(part) for part in ("outcome", *e.get("loc", ())))
        found = e.get("input")
        found_text = json.dumps(found, ensure_ascii=False, default=str) if found is not None else "nothing"
        errors.append({"code": "OUTPUT_MALFORMED", "path": path, "problem": f"{e.get('msg')}; found {found_text[:200]}",
                       "expected": "the value the output_schema declares at this path"})
    return errors or [{"code": "OUTPUT_MALFORMED", "path": "outcome", "problem": str(exc)[:1200],
                       "expected": "an object matching the output_schema in the input"}]


def make_wire_validator(parse: Callable[[str], Any]) -> Validator:
    """BOOTSTRAP_ANALYSIS: the operation's wire model (the operation bridge's parse, Pydantic), nothing else."""

    def validate(outcome: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
        try:
            parse(json.dumps(outcome))
        except Exception as exc:
            return _wire_errors(exc), []
        return [], []

    return validate


def make_lint_validator(parse: Callable[[str], Any], body_of: Callable[[Any], tuple[str, str] | None],
                        lint: Callable[[str], Any]) -> Validator:
    """DRAFT_PROMPT and DRAFT_PLAN: the wire model, then the host's pseudocode notation lint on the body ``body_of``
    names ((field, text), or None for an outcome with no body, a blocked draft). Each violation is one error, in the
    lint's own wording."""

    def validate(outcome: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
        try:
            parsed = parse(json.dumps(outcome))
        except Exception as exc:
            return _wire_errors(exc), []
        named = body_of(parsed)
        if named is None:
            return [], []
        field_name, text = named
        return [{"code": "PDL_LINT", "path": f"outcome.{field_name}", "problem": violation,
                 "expected": "a body that meets the pseudocode notation requirement"}
                for violation in lint(text).violations], []

    return validate


def event_view(record: dict[str, Any]) -> dict[str, Any]:
    """An AGENT_TOOL_CALL event payload: the record with long text trimmed (the full text stays in the trace)."""
    view = {k: v for k, v in record.items() if k not in ("arguments", "output", "outcome")}
    for key in ("arguments", "output"):
        if isinstance(record.get(key), str):
            view[key] = record[key][:2000]
    return view
