# ADR-0024: Operation Profiles

## Status
**Proposed.** Future work; not implemented in 2.6.0rc1. Date: 2026-10-02. Deciders: project maintainers.

- Direction: [`TARGET_ARCHITECTURE.md`](../../TARGET_ARCHITECTURE.md) §4.2 and §5. Current behaviour: [`ARCHITECTURE.md`](../../ARCHITECTURE.md) §2.1, §3.3, §6.
- Would amend: [ADR-0022](0022-default-reasoning-high-pre-execution.md) (the per-model reasoning mapping becomes a profile default) and the model class matrix of [ADR-0006](0006-bounded-pre-execution-reasoning.md). Related: [ADR-0012](0012-system-1-decision-models-via-rlcd.md), [ADR-0020](0020-system-1-environment-conditioned-refusal-routing.md), [ADR-0023](0023-taskmaster-host-interface-and-event-contract.md) (carries budgets and the environment report).
- Requirements: `PROF-*` in `REQUIREMENTS.md` (planned; this section will list them).

## Context
Output tokens are usually discussed as a cost. In PDLt they are mainly a **latency and capability-fit** problem: they decide which providers and models are practical at all. A provider optimized for fast reasoning is only useful if a whole session stays short, and a fast System 1 model (Jev) is nearly free but cannot do substantial reasoning.

Evidence from 762 recorded catalogue sessions on `openai/gpt-oss-120b` (2026-10-02):

- Output per session: median about 3.1k tokens and 8 s of model time; 90th percentile about 11.7k and 31 s; worst about 138k and 888 s.
- By number of `EXECUTE` calls: one call, median 3.1k and 8 s (581 sessions); two, 4.0k and 26 s (87); three or more, 11.4k and 66 s (26).
- 11% of sessions exceeded 30 s of model time; 56 of those 82 involved at least one verification repair. **The slow tail comes from verification and repair, not from long answers.**
- The three pre-execution operations produce a median 62% of a session's output. At the ADR-0022 default (high reasoning before execution) a trivial request spends about 3.6k output tokens before execution, 89% of it hidden reasoning; `EXECUTE` is about 4% reasoning.

Today four different concerns are set in different places and not as one coherent choice:

| Concern | Where it is set today |
|---|---|
| Reasoning depth | Hardcoded per model family (ADR-0022's gpt-oss mapping), overridable per operation by `--api-reasoning-operation` |
| Artifact length | Fixed by the standards and contracts |
| Verification depth | Witness requirement from System 1's problem class; repairs from the routed execution tier (1 or 2), overridable by `--max-repairs` |
| Model routing | One `--model`, overridable per operation by `--api-model-operation`; provider order by `--api-providers` (OpenRouter names) |

There is no session time or token budget, no description of what a provider can do (structured output, reasoning control, throughput, local or remote), and adding a model family means editing the reasoning mapping in code. System 1 is a fixed remote endpoint; when it is unavailable, boundary routing silently does not run.

## Decision
Introduce **operation profiles**: a declared configuration that sets four independent axes per operation, plus session budgets, and route models by capability.

1. **Separate axes.** Each operation (`BOOTSTRAP_ANALYSIS`, `DRAFT_PROMPT`, `DRAFT_PLAN`, `EXECUTE`, review interpretation, and so on) has:
   - *reasoning depth* (a provider-neutral level mapped to each provider's own control),
   - *artifact length* (a budget for the visible artifact, within what the standards require),
   - *verification depth* (witness required or not; repairs allowed),
   - *capability class* (System 1 decision, light structured call, reasoning, code generation).
2. **Provider capability descriptors.** Each configured provider declares what it supports: structured output and schema strictness, reasoning control, context size, typical throughput, local or remote, and cost class. Routing chooses a provider for an operation's capability class from these descriptors, not from model names in code.
3. **Named profiles.** A profile sets the axes for every operation at once. Initial profiles: `fast` (low reasoning, no repair beyond the first, routes to high-throughput providers), `balanced` (today's defaults: the ADR-0022 mapping becomes this profile), and `verified` (witness-first, tier-scaled repairs). Per-operation flags remain as overrides.
4. **Session budgets.** A session may carry a wall-clock and token budget. When a budget would be exceeded, the controller stops further repairs and closes with an explicit **unverified** outcome that states why, instead of continuing. Budgets and the outcome are reported through ADR-0023.
5. **System 1 as a declared capability.** System 1 is configured like any provider. Each deployment declares what boundary routing does when System 1 is unavailable (`refuse`, or `proceed` as today), and the session's environment report states it.
6. **Neutrality is preserved.** Profiles change resources, never the task or the method: no profile may add guidance about how to solve a task (`GUARD-01`, `GUARD-04`). Profiles are recorded in run metadata so results remain comparable.

### Incremental delivery
1. Record the effective axes per operation in run metadata (extending ADR-0022's `reasoning_effective`).
2. Add session budgets and the unverified closure.
3. Add provider capability descriptors; route by capability with today's configuration as the default.
4. Add named profiles; make `balanced` the default with unchanged behaviour.
5. Make System 1 configurable and declare its absence behaviour.

## Options considered

### A. Treat output tokens as a cost knob (lower defaults)
| Dimension | Assessment |
|---|---|
| Complexity | Low |
| Latency | Helps the median, not the repair-driven tail |
| Provider fit | Unchanged |

**Pros:** simple. **Cons:** degrades drafting quality (ADR-0022 records what all-low reasoning did to plans) without addressing the tail, which comes from repairs.

### B. Per-operation flags only (today, extended)
| Dimension | Assessment |
|---|---|
| Complexity | Low to medium |
| Latency | Tunable by experts |
| Provider fit | Manual; model names stay in code |

**Pros:** no new concepts. **Cons:** no budgets, no capability routing, and every deployment re-derives a working configuration.

### C. Operation profiles with capability routing and budgets (chosen)
| Dimension | Assessment |
|---|---|
| Complexity | Medium |
| Latency | Bounded by budgets; profiles target fast providers explicitly |
| Provider fit | New providers are described, not coded |

**Pros:** each axis is set for its own reason; fast providers become usable for the `fast` profile; local and subscription providers fit the same model. **Cons:** profiles add configuration surface; results must record the profile to stay comparable.

## Consequences
- **Easier:** using fast or local providers deliberately; bounding subagent cost; adding a model family without code changes; explaining why a run was slow.
- **Harder:** comparing runs made under different profiles (mitigated by recording the profile).
- **Unchanged:** the protocol stages, review gates, witness authority and guardrails.
- **Revisit:** the default boundary-routing behaviour when System 1 is unavailable (TARGET_ARCHITECTURE §8), and whether review interpretation should move further to System 1.

## Out of scope
The host contract that carries budgets and reports (ADR-0023); tool capabilities (ADR-0025); profiles shipped inside workflow packs (ADR-0026).
