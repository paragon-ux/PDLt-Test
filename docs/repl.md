# REPL and headless runs

`pdlt` is PDLt's command-line interface. It runs in two ways:

- **Interactive (the REPL):** you type tasks and commands at a `>` prompt.
- **Headless:** with `--non-interactive`, it reads tasks from a pipe or a file, runs them, and exits with a code a script or CI job can test.

Both use the same library layer as the [Python API](api.md), so a task behaves the same way in each. Install PDLt and set `OPENROUTER_API_KEY` first: see your host's page ([Windows](hosts/windows.md), [Linux](hosts/linux.md), [macOS](hosts/macos.md)).

Commands below are shown for **bash** (Linux, macOS) and **PowerShell** (Windows) where they differ. Text after a `>` prompt is what you type into the REPL itself, not into the shell.

## Start the REPL

| Command | What it does |
|---|---|
| `pdlt` | Lists your 10 most recent sessions and asks which to open (`n` or Enter for a new one) |
| `pdlt --new-session` | Starts a new session without asking |
| `pdlt --session-id my-work` | Opens the session named `my-work`, creating it if it does not exist |
| `pdlt --review` | Stops at the prompt and the plan for your review before anything runs (see "Review modes") |
| `pdlt --model openai/gpt-oss-120b` | Uses another model (the default is `nvidia/nemotron-3-super-120b-a12b:free`) |

On start it prints:

```text
PDLt REPL started (v2.6.0).
Send input to the SessionEngine. Review gates accept /confirm, /revise <feedback>, /stop or /cancel.
Commands: /help (full roster), /paste (multi-line), /status, /quit
[no-review] No-review mode: ON (review gates disabled; ...)
>
```

If it also prints `[warn] code execution unavailable: ...`, the sandbox is not available on this machine and no program will run: see your host's page, step 4.

## Give it a task

Type the task in plain words at the `>` prompt and press Enter:

```text
> Count the primes below 1000 and print the count.
```

For a task over several lines, type `/paste`, paste the text, and finish as the REPL tells you; or wrap the text in `"""` on lines of their own.

What comes back depends on the request:

- **A task PDLt carries out:** it restates the task, writes and runs a program in the sandbox, checks the result, and publishes it with its provenance (how far the host could establish it).
- **A request outside its bounds** (for example one that needs the network): System 1 refuses it, with the reason.
- **A conversational message:** a direct reply, with no protocol run.

## Review modes

| Mode | Start with | Toggle in the REPL | What happens |
|---|---|---|---|
| No review (the default) | `pdlt` or `--no-review` | `/no-review on` | Runs straight through. The interpretation is shown as an unconfirmed working note. |
| Review | `--review` | `/no-review off` | Stops at the prompt pseudocode and again at the plan. Answer `/confirm` to go on, `/revise <what to change>` for a new draft, or `/stop` to cancel. |
| Fast | `--fast` (implies `--review`) | `/fast on` | Both artifacts are shown; one the host has no findings on is accepted without waiting, and one with findings stops for you. |

## Commands at the `>` prompt

| Command | Effect |
|---|---|
| `/help` | The full list |
| `/confirm` | Accept the prompt or plan under review |
| `/revise <feedback>` | Ask for a revised prompt or plan |
| `/stop`, `/cancel` | Cancel the current task |
| `/paste` | Multi-line input (or `"""` ... `"""`) |
| `/status` | The session's current state, read-only |
| `/session` | The current session's folder |
| `/no-review [on\|off]`, `/fast [on\|off]` | Switch review mode (above) |
| `/model [name]` | Show or change the model |
| `/timeout [seconds]` | Show or change the time limit for one model call |
| `/tokens [on\|off]` | Show token counts per call |
| `/sessions [prune <days>]` | List sessions, or delete those older than the given number of days |
| `/new`, `/resume <session-id>` | Start a new session, or switch to another |
| `/transcript [path]` | Show or change where the transcript is written |
| `/workdir [path]` | Show or change the worker's working folder |
| `/worker <name>` | Switch to another registered worker provider ([Extensions SDK](extensions.md#providers)) |
| `/dev [on\|off\|status\|diagnose\|set\|get]` | Developer mode: telemetry and diagnostics |
| `/quit` | Leave |

`/config` and `/sandbox` apply only to the deprecated Codex worker (`--worker codex`, to be removed: ledger L114). `/sandbox` there is Codex's own setting, not PDLt's program sandbox.

## Headless runs

Headless mode never asks a question. It reads lines from standard input, treats each as a message, and exits when the input ends. The exit code is the outcome of the last task: an earlier task that was cancelled does not change it. A harness or provider error ends the run at once (exit 4), and so does a pause the input does not answer (a review gate, exit 2; a request for input, exit 3). When each task must pass on its own, run one task per process.

**One task from a pipe:**

bash:

```bash
printf '%s\n' "Count the primes below 1000 and print the count." | pdlt --non-interactive --new-session
echo $?
```

PowerShell:

```powershell
"Count the primes below 1000 and print the count." | pdlt --non-interactive --new-session
$LASTEXITCODE
```

Each line of piped input is a separate message, so a task that spans several lines must come from a file.

**A task from a file** (any length; UTF-8). `--prompt-file` sends the whole file as one message; the piped `/quit` ends the session afterwards:

bash:

```bash
printf '/quit\n' | pdlt --non-interactive --new-session --prompt-file task.txt
```

PowerShell:

```powershell
"/quit" | pdlt --non-interactive --new-session --prompt-file task.txt
```

`--prompt "text"` does the same with the text given on the command line.

**With review gates.** Headless review mode stops at the first gate and exits with 2 unless the input confirms it. To accept both reviews, pipe the confirmations after the task:

```bash
printf '%s\n' "Count the primes below 1000 and print the count." /confirm /confirm | pdlt --non-interactive --new-session --review
```

### Exit codes

| Code | Meaning | What to do |
|---|---|---|
| 0 | Closed with a result the host established or contract-checked (`CLOSED_SUCCESS`); a direct reply; or a published boundary refusal | Nothing, unless the result must be verified: then check its provenance (below) |
| 1 | Cancelled, or failed closed after its repairs (`CLOSED_CANCELLED`) | Read the transcript for the findings |
| 2 | Stopped at a review gate, or at another non-terminal stage | Pipe `/confirm` lines, or run without `--review` |
| 3 | Waiting for input the task needs (`WAITING_INPUT`) | Supply it in a follow-up message |
| 4 | Harness or provider error: never a task outcome. A `[harness-error]` JSON line on standard error says where | See [Reference: when something fails](reference.md#when-something-fails) |
| 5 | Published, but the host could not establish it (`CLOSED_UNVERIFIED`) | Treat the result as unverified; its `provenance.json` says what is missing |
| 130 | Interrupted (Ctrl+C) | Nothing |

A headless run that ends anywhere but `CLOSED_SUCCESS` also prints a `[headless halt]` or `[headless close]` line on standard error naming the stage.

### Check the verification level in CI

Exit 0 also covers a result that passed only the contract checks, a direct reply and a refusal. A CI step that needs more checks the published result's `provenance.json` as well: its `verification.level` is `host_verified`, `contract_checked` or `unverified`, and a direct reply or a refusal publishes none. Run one task per process in a fresh `--workspace-root`, so the folder holds that task's provenance only. These steps require `host_verified`; use the level your step needs.

bash:

```bash
root=$(mktemp -d)
printf '%s\n' "Count the primes below 1000 and print the count." | pdlt --non-interactive --new-session --workspace-root "$root"
code=$?
[ "$code" -eq 0 ] || exit "$code"
prov=$(find "$root" -name provenance.json | head -n 1)
[ -n "$prov" ] || { echo "no published result (a direct reply or a refusal)" >&2; exit 1; }
level=$(python -c "import json, sys; print(json.load(open(sys.argv[1], encoding='utf-8'))['verification']['level'])" "$prov")
[ "$level" = host_verified ] || { echo "not host-verified: $level" >&2; exit 1; }
```

PowerShell:

```powershell
$root = Join-Path ([IO.Path]::GetTempPath()) ([guid]::NewGuid())
"Count the primes below 1000 and print the count." | pdlt --non-interactive --new-session --workspace-root $root
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$prov = Get-ChildItem $root -Recurse -Filter provenance.json | Select-Object -First 1
if (-not $prov) { Write-Error "no published result (a direct reply or a refusal)"; exit 1 }
$level = (Get-Content $prov.FullName -Raw -Encoding utf8 | ConvertFrom-Json).verification.level
if ($level -ne "host_verified") { Write-Error "not host-verified: $level"; exit 1 }
```

From Python, the same level is `result.provenance["verification"]["level"]` ([Python API](api.md)).

## Frequently used flags

`pdlt --help` lists every flag. These are the ones most setups need:

| Flag | Effect |
|---|---|
| `--new-session`, `--session-id NAME` | A new session, or a named one (created or resumed) |
| `--non-interactive` | Headless: no questions, exit code at the end |
| `--prompt TEXT`, `--prompt-file PATH` | A first message from the command line or a file |
| `--exit-on-close` | Exit as soon as a task closes, without waiting for more input |
| `--model NAME` | The task model (any OpenRouter model id) |
| `--review`, `--fast`, `--no-review` | Review mode (above) |
| `--sandbox auto\|native\|container\|audit-only` | Program confinement; `audit-only` turns the OS sandbox off and prints a warning; there is no `off` ([Sandbox guide](SANDBOX.md)) |
| `--task-type NAME` | Pin a registered task type instead of letting System 1 classify each request ([Extensions SDK](extensions.md)) |
| `--max-repairs N` | Repair attempts after a failed check; `0` stops at the first failure |
| `--no-tier-d1` | Do not feed sandbox failures back to the model as repairs |
| `--api-providers A,B` | Only these OpenRouter providers, in this order ([Providers](providers.md)) |
| `--api-reasoning-effort none\|low\|medium\|high` | Reasoning effort for every operation |
| `--workspace-root PATH` | Where sessions are kept (default below) |
| `--transcript PATH` | Where the transcript is written |
| `--dev` | Developer mode: per-call telemetry |
| `--agent-tools` | In-call tools inside model operations: `run_python` and `read_attempt` on EXECUTE_UNCONFIRMED, and checked submissions ([MCP and in-call tools](mcp/EXTERNAL_TOOLS.md)) |
| `--agent-tools-exclude TOOL[,TOOL]` | With `--agent-tools`, withhold the named tools, for an ablation. A withheld submission tool means the operation answers in its message, and the host checks the reply after the call; an operation with every tool withheld makes a plain call |
| `--withhold-execution-context` | L148 A/B: BOOTSTRAP_ANALYSIS, DRAFT_PROMPT and DRAFT_PLAN (and their revisions) receive only their own instructions, without the execution environment or EXEC-* clauses |
| `--ablate-unconfirmed PART[,PART]` | L149 ablation, a measurement: change what EXECUTE_UNCONFIRMED receives. `normative`: no standard clauses or guidance block; `framing`: no execution environment, EXEC-* clauses, or code, tool and witness wording; `notation`: the working notes in plain prose; `order`: the deliverable before the working notes; `entities`: no TASK_ENTITIES (the bootstrap's extraction). Other operations are unchanged |
| `--draft-execute` | Draft a typed execution brief before EXECUTE on tasks that are or need an algorithm or a calculation |
| `--no-api-structured-output` (alias `--no-structured-output`) | Send no output-format constraint to the provider. On by default: each operation gets a JSON schema or JSON mode, as the API worker chooses |
| `--api-reasoning-operation OP=EFFORT`, `--api-model-operation OP=MODEL` | Reasoning effort or model for one operation; repeatable |
| `--max-output-tokens N` | Output-token cap per call, reasoning included (default 16384) |
| `--worker-timeout SECONDS` | Worker timeout (default 600) |

Two subcommands sit beside the REPL: `pdlt version` prints the version, and `pdlt init` seeds the operation contracts into `~/.pdlt` (`--local` for `./contracts`), which you only need to customise them.

## Where sessions are kept

In a source checkout, `runs/live-sessions/<session>/`; otherwise `~/.pdlt/runs/live-sessions/<session>/` (on Windows, `$HOME\.pdlt\runs\live-sessions\`). `--workspace-root` chooses another folder. Each session folder holds the workspaces, the transcript, `worker-progress.log` and `call-trace.jsonl`. A published result is in its turn's `stages/50_execution/output/` folder: `current.md`, `program-output.json` and `provenance.json`.
