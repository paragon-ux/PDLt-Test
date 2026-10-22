# Release Audit: 2.6.0 (retrospective)

**Written:** 2026-10-21, after the release, on the local branch `claude/retrace-gemini` (ledger L133, L136). **Scope:** the released tag `v2.6.0` (`4f0760e9`), what it contains, how it was released, the defects found in it since, and the checks that never ran for it. Severity as in [2.6.0rc1](RELEASE_AUDIT_2.6.0rc1.md): **High** misleads users about safety or behaviour; **Medium** is a visible defect; **Low** is cleanup.

Nothing in this audit changes the release. The tag, the GitHub release and the PyPI files stay as they were published.

## 1. What 2.6.0 is

| Fact | Evidence |
|---|---|
| Tag `v2.6.0` points at the merge commit `4f0760e9` (PR #4, a merge commit, 2026-10-17 23:14 UTC). | `git tag --points-at 4f0760e9` |
| Released by Gemini 4 Argon (Antigravity) after the previous Claude session stopped at `4e335a33`. | L133 |
| The release workflow run `39078337432` succeeded: the whole `ci.yml` through `workflow_call`, the tag/version check, one build, `twine check --strict`, a wheel smoke test outside the repository, then trusted publishing. | read-only `gh` check, 2026-10-21; `.github/workflows/release.yml` |
| PyPI `pdl-taskmaster` 2.6.0: wheel and sdist uploaded 2026-10-17 23:24 UTC, licence MIT, `Requires-Python >=3.10`. Earlier releases on PyPI: 2.4.0, 2.5.0, 2.5.1. | `https://pypi.org/pypi/pdl-taskmaster/json`, 2026-10-21 |
| `src/` at the tag is byte-identical to `src/` at `4e335a33`. The three commits between them change tests, docs, the `pyproject.toml` extras and the ledger only. | `git diff 4e335a33 v2.6.0 -- src` is empty |
| The features of the minor release are the Python API and the extensions SDK; the version moved from 2.6.0rc1 (never published) to 2.6.0. | L128 |
| The catalogue baseline (L127) ran at `4c2e2f00`. The source changes between `4c2e2f00` and the tag are the version string, `pdlt --help` text, a default `repo_root` for registered providers, and a byte-order-mark fix for piped standard input in the REPL and the MCP server. None changes what the model receives. | `git diff 4c2e2f00 4e335a33 -- src` |
| The documentation site serves the build from `main`: `/`, `api/`, `hosts/windows/`, `hosts/linux/`, `hosts/macos/`, `repl/`, `reference/`, `releasing/`, `SANDBOX/`, `mcp/EXTERNAL_TOOLS/` and `benchmarks/` return 200 (Zensical 0.0.68). `api/` carries the `PDLT_STANDARDS_PATH` text that only `main` has, so the pages that returned 404 on 2026-10-17 (L126) are deployed. | read-only fetch, 2026-10-21 |

## 2. Defects found in 2.6.0 since the release

Each is fixed or recorded on `claude/retrace-gemini`; none is released.

| ID | Severity | Area | Defect | Where it is handled |
|---|---|---|---|---|
| RB-01 | Medium | In-call tools (`--agent-tools`, opt-in) | The in-call submission check (`make_validator`) has no hard-coded-answer rule, while the host's closing check does (`_witness_written_in_program`, L113/L119). A submission whose program prints a witness it writes out itself is accepted in the call, then flagged by the host at close (run 01-03 r3 of L132). The two checks disagree. | L139 |
| RB-02 | Medium | MCP server | `initialize` answers only `2025-06-18`, whatever the client asks. The server runs tools before `initialize`. Neither the call log nor the session sandbox is closed at exit. | L138 |
| RB-03 | Medium | Catalogue runner | `run_catalogue.py` passes `--api-structured-output` to every route, has no way to turn it off, and records `rules.structured_output: true` for the Control route, which never constrains output. | L137 |
| RB-04 | Medium | Provenance | Under STANDARD_EXECUTION, Tier D1 feeds back only genuine `PROGRAM_FAILED` failures. A program stopped by its memory, wall-clock or step budget is discarded silently, and the closed turn's caveat says only that the host "ran its programs" (run 06-06 of L127). | L140 |
| RB-05 | Low | Docs, REPL help | The README and `pdlt --help` cite ADR-0029 for the no-review default; ADR-0029 is the in-call tools decision, and the default comes from L94. | L141 |
| RB-06 | Low | Tests | The parity test, as released, pins `sandbox.PYTHON_VERSION` to 3.11 for the whole run and rewrites the fixture's recorded version. That hides interpreter differences instead of checking them. | L134 |
| RB-07 | Low | Tests | `b52ba73f` raised the audit-layer confinement test's limit to 60 s for a CI-only failure that was never investigated. It passes 10 of 10 in about 1 s locally. | L135 (not taken) |
| RB-08 | Low | Tests | The container escape tests fail on a Windows host with Docker Desktop: they hand Windows paths to a program that runs in a Linux container. This is a test defect; confinement holds, and no host file is reached. | L135 |
| RB-09 | Low | Scanner | The benchmark-contamination scan reads `11-05` in the date `2024-11-05` as a prompt ID. On Gemini's uncommitted branch this led to removing a protocol version; the scanner is what needs fixing. | L138 |

## 3. Checks that never ran for 2.6.0

- **`sandbox.yml` within the release workflow.** The release workflow calls `ci.yml` only. `sandbox.yml` ran separately and succeeded on PR #4's head (`b52ba73f`) and on the pushes of `main` and `v2.6.0` (`4f0760e9`). At `3e0a0388` it had failed once on `windows-latest / py3.13`, a 5 s wall-clock stop in the audit-layer test that `b52ba73f` answered with a 60 s limit (RB-07). Read-only `gh`, 2026-10-21.
- **A live "receives" check after the last change to what the model receives.** None was needed: no such change happened between the baseline (`4c2e2f00`) and the tag.
- **`run_catalogue.py --fail-fast` before the merge (AGENTS.md).** It is not recorded as run. The full catalogue baseline (L127) ran at `4c2e2f00` on the same request-side code.
- **An independent review of Gemini's three commits before they were tagged.** The retrace (L133–L144) is that review, made after the release.
