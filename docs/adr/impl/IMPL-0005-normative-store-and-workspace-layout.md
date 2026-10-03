# IMPL-0005: Normative Store, Workspace and Session Layout

## Status
**Accepted.** Implements [ADR-0008](../0008-context-and-session-management.md) and decisions 1–2 of [ADR-0011](../0011-in-memory-vfs-and-microvm-sandboxing.md). Recorded 2026-10-03 from the 2.6.0rc1 code; decisions dated 2026-09-17 and 2026-09-26.

## Context
ADR-0008 separates a versioned normative store from dynamic, on-demand workspaces, with a session → turn → invocation hierarchy. ADR-0011 keeps active context flow in memory and persists at turn boundaries. This record holds the paths, files and formats.

## Decision (as implemented)
- **Normative store resolution** (`runtime/normative_store.py`), in order:
  1. the `PDLT_STANDARDS_PATH` environment variable;
  2. `<candidate repo>/contracts/`;
  3. `~/.pdlt/versions/<version>/contracts/`;
  4. the copy bundled in the package.

  A project pins its version with `.pdlt-version` or `pdlt.json`. Replay hashing is over the serialized clause text, not over disk paths. `pdlt init` seeds a copy.
- **Workspaces.**
  - A workspace starts empty except for state and event directories.
  - Stage directories, `stages/<stage>/input/<NNNN-operation>/` and `.../output/<NNNN-operation>/`, are created when an operation runs.
  - Current artifacts are `current.json` and `current.md`; events go to `events.jsonl`.
  - Turns are `turns/turn_NNN/`. Sessions live under `runs/live-sessions/<session-id>/`, with `session.json`, `transcript.log`, `worker-progress.log` and `call-trace.jsonl`.
- **In-memory flow** (`runtime/workspace.py`, `MemoryWorkspaceRun`).
  - Stage files are held in an in-memory map and also written to disk, replace-on-write (`fileio.replace_text`), without `fsync`.
  - Events are appended to `events.jsonl` and flushed without `fsync`.
  - When a turn closes or is interrupted (`CLOSED_SUCCESS`, `CLOSED_CANCELLED`, `INTERRUPTED`), `flush_turn_archive` writes `turn_archive.json`: status, deliverable hash, and every event read back from the durable log.

## Divergence from ADR-0011 decision 2
ADR-0011 says intermediate stage steps are not written as loose files, and that a turn persists as one SQLite record or compressed archive. The code still writes each stage file, without `fsync`, and adds a per-turn JSON archive. `--debug-preserve-workspaces` does not exist. The loose files are what the graders, viewer and replay read today.

## Evidence
- **Template copying before ADR-0008:**
  - every workspace got 35 files;
  - removing the templates cut the files created per task by over 85%.
- **Before ADR-0011:**
  - every file write was `mkstemp` followed by `fsync`, 60–100 per five-stage turn: 1.5–4 s of blocking I/O per turn on NTFS;
  - the 162-trial F6.3 suite created over 87,000 files.

## Verification
- `tests/test_interruptions.py`: turn archive on interrupt, and replace-on-write.
- Resume tests in `tests/test_repl_integration.py`.
