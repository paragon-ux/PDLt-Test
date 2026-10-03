# ADR-0026: Extension and Workflow Model

## Status
**Proposed.** Future work; not implemented in 2.6.0rc1. Date: 2026-10-02. Deciders: project maintainers.

- Direction: [`TARGET_ARCHITECTURE.md`](../../TARGET_ARCHITECTURE.md) §4.4. Current behaviour: [`ARCHITECTURE.md`](../../ARCHITECTURE.md) §7.
- Builds on: [ADR-0008](0008-context-and-session-management.md) (normative store). Depends on [ADR-0023](0023-taskmaster-host-interface-and-event-contract.md), [ADR-0024](0024-operation-profiles.md) and [ADR-0025](0025-agentic-capability-boundary.md), whose seams a workflow pack bundles. Bound by the guardrails (`GUARD-01` to `GUARD-05`).
- Requirements: `EXT-*` in `REQUIREMENTS.md` (planned; this section will list them).

## Context
PDLt will be publicly released, and users will want it for many kinds of work: research, coding, mathematics, writing, Q&A, general agents, and domain-specific workflows. Customization is therefore a first-class concern. The risk is that the only way to customize today is to change internals, which makes it easy to break guarantees by accident.

What exists today:

- **Contracts and standards are already separate from code** (`contracts/`, bundled under `src/pdl_taskmaster/contracts/`), and `NormativeStore` resolves them in order: `PDLT_STANDARDS_PATH`, `<candidate repo>/contracts/`, `~/.pdlt/versions/<version>/contracts/`, then the bundled copy. `pdlt init` seeds a copy.
- An override **replaces the whole contract set**, is selected by directory location alone (the candidate repo defaults to the current directory), and is checked for structure only (`StandardRegistry`). The SHA-256 manifest check is a test (`GUARD-05`), not a load-time check, and nothing checks that an override is compatible with the running core.
- Each compiled projection records the SHA-256 of every clause it used, so the provenance of an override is traceable after the fact.
- **Operation prompts are Python source** (for example in `runtime/operation_bridge.py`, `runtime/wire_payloads.py` and `providers/api_worker.py`), so changing how an operation is asked means forking the package.
- There is no unit for "a workflow": nothing bundles the model configuration, verification expectations, tools and prompts that suit, say, research rather than mathematics.

A specific constraint applies. `GUARD-01` forbids the harness from injecting methods or hints. Workflow-specific guidance written by a user is user-originated content, which the protocol already accepts (`CARRIED_APPROACH_SOURCES`); guidance shipped with PDLt is harness content and must meet the guardrails.

## Decision
Adopt three tiers with different change processes.

1. **Core (closed).** `MechanicalController`, review gates, wire schemas, witness authority, confinement and the guardrails. Not extensible; changed only by ADR. Extensions cannot disable or weaken core checks; they can only add constraints.
2. **Contracts (versioned and validated).**
   - Each contract set declares its version and the range of core versions it supports.
   - At load, the host validates the manifest hashes, the schema of every contract file, and core compatibility, and refuses an incompatible set with a clear message (fail closed).
   - Overrides are layered: a user overlay changes named clauses or files and inherits the rest, instead of replacing the whole set.
   - The resolved set, and every overlay applied, is reported in the environment report (ADR-0023) and recorded per projection as today.
3. **Workflow packs (open).** A pack is a named, versioned bundle for a kind of work, described by a schema-validated manifest. It may contain:
   - an operation profile (ADR-0024),
   - capability grants such as a project-root access level and permitted tools (ADR-0025),
   - verification checkers registered by typed domain (today none are shipped),
   - prompt fragments as data, within slots the core defines,
   - presentation hints for clients (ADR-0023).
4. **Prompts become data.** Operation prompts move from Python source to versioned templates with defined slots, so a pack can supply fragments without forking. The core owns the template structure and the wire schema.
5. **Discovery and selection.** Packs are discovered from installed Python entry points and a user directory (for example `~/.pdlt/packs/`), selected explicitly per session, and listed by a CLI command. The default pack reproduces today's behaviour.
6. **Integrity.** A pack's content is recorded as user-originated, with its name, version and hash, in every projection that uses it. Packs shipped with PDLt pass the same anti-overfitting gate as the harness. A conformance kit (`pdlt pack validate`) checks a pack's manifest, schemas, compatibility, and that it does not weaken core checks.

### Incremental delivery
1. Load-time validation of contract manifests, schemas and core compatibility; clear refusal on mismatch.
2. Layered contract overlays and reporting of the resolved set.
3. Move operation prompts to versioned templates with slots, with no behaviour change.
4. Pack manifest schema, discovery and explicit selection, with the default pack equal to today.
5. Conformance kit and first non-default packs.

## Options considered

### A. Document the internals and let users edit them
| Dimension | Assessment |
|---|---|
| Complexity | Low |
| Safety of customization | Poor: any edit can break a guarantee silently |
| Upgradability | Poor: forks diverge |

**Pros:** nothing to build. **Cons:** every customization is a fork; integrity guarantees cannot be checked.

### B. Contract overrides only (today, with validation added)
| Dimension | Assessment |
|---|---|
| Complexity | Low to medium |
| Safety of customization | Better for standards |
| Expressiveness | Cannot change profiles, tools, checkers or prompts |

**Pros:** builds on ADR-0008. **Cons:** a workflow needs more than standards; prompts stay in code.

### C. Closed core, versioned contracts and workflow packs (chosen)
| Dimension | Assessment |
|---|---|
| Complexity | Medium to high |
| Safety of customization | Validated at load; core cannot be weakened |
| Expressiveness | A workflow is one installable, versioned unit |

**Pros:** safe defaults, explicit extension points, upgradable customizations, traceable provenance. **Cons:** schemas and compatibility rules to maintain; moving prompts to data is a significant refactor.

## Consequences
- **Easier:** sharing workflows; customizing without forking; telling users exactly what they may change.
- **Harder:** maintaining manifest and template schemas across core versions.
- **Unchanged:** the protocol, the guardrails, and the behaviour of a session with no pack selected and no override present.
- **Revisit:** how pack guidance is presented to the model so that it remains user-originated under `GUARD-01` (TARGET_ARCHITECTURE §8).

## Out of scope
The host contract, profile semantics and capability boundary themselves (ADR-0023 to ADR-0025); a pack registry or marketplace.
