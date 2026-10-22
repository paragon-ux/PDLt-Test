# Linux

This page sets PDLt up on Linux, from nothing to a first verified task. Every command is for **bash** in a terminal. Lines starting with `#` are comments; you do not need to type them.

**What it does here.** PDLt runs model-written programs under **Landlock**, the Linux kernel's own access control for unprivileged processes. Nothing extra is installed for it, and no root access is needed.

**At the end you will have:** PDLt installed in a virtual environment, the `pdlt` command working, the sandbox confirmed, and one task run end to end.

## 1. Prerequisites

| Need | Detail |
|---|---|
| Linux kernel 5.13 or later, with Landlock enabled | Many current distributions enable it; step 4 tells you for certain (CI uses GitHub's `ubuntu-latest`). On an older kernel PDLt fails closed: it runs no program. |
| Python 3.10 to 3.14, with `venv` | On Debian and Ubuntu, `venv` is a separate package: `sudo apt install python3-venv`. |
| git | Only to install from source: `sudo apt install git` (Debian, Ubuntu) or `sudo dnf install git` (Fedora). |
| An OpenRouter API key | Only for step 5. Steps 1 to 4 need none. |

**Check:**

```bash
uname -r              # the kernel version: 5.13 or later
python3 --version     # 3.10 to 3.14
```

## 2. Install

Pick one. Both create a virtual environment so PDLt does not touch your system Python.

**From PyPI** (a released version; 2.6.0 or later has the Python API and the extensions SDK). Run this in the folder where you want the environment, for example your home folder:

```bash
cd ~
python3 -m venv pdlt-env
source pdlt-env/bin/activate
python -m pip install --upgrade pip
python -m pip install "pdl-taskmaster>=2.6.0"
```

**From source** (to run the test suite, the evaluation catalogue, or change the code):

```bash
cd ~
git clone https://github.com/paragon-ux/PDLt-Test.git
cd PDLt-Test
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

After activation, your prompt starts with `(pdlt-env)` or `(.venv)`. Every later command on this page assumes that environment is active. In a new terminal, run the `source` line again first.

**Check:**

```bash
pdlt version
```

Expected: one line such as `pdl-taskmaster 2.6.0 (protocol specification: v2, manifest: C0-R4-1.0)`.

## 3. Verify offline

**From source:** run the offline test suite and the integrity gate from the `PDLt-Test` folder. No API key or network is used: models are scripted or replayed from recordings.

```bash
python -m pytest -q -n auto
python -m pytest tests/test_harness_anti_overfitting.py -W error
```

Expected: the first ends with a line like `1321 passed, 42 skipped` (the numbers change as tests are added; skips are backends this machine does not have, such as AppContainer). The second must report every test passed, with no warnings or skips. Any `failed` or `error` means the install is not sound.

**From PyPI:** the tests are not in the package. Run an empty headless session instead:

```bash
printf '/quit\n' | pdlt --non-interactive --new-session --workspace-root /tmp/pdlt-check
echo $?
```

Expected: it prints a short start-up banner, then `0`.

## 4. Check the sandbox

```bash
python -c "from pdl_taskmaster.api import create_sandbox; s = create_sandbox('auto', label='setup-check', require_confined=True); r = s.run_code('print(6 * 7)'); print(s.backend_name, r.exit_code, r.stdout.strip()); s.close()"
```

Expected: `landlock 0 42`.

If it raises `SandboxNotConfined`, the message says why. `Landlock is not available on this kernel (...): it needs Linux 5.13+ with Landlock enabled in the LSM list` means the kernel is too old, or was built or booted without Landlock: upgrade the kernel, enable `landlock` in the boot-time `lsm=` list, or use the container backend below. From source, the full escape suite is `python -m pytest tests/test_confinement.py -v`.

## 5. Configure a model

PDLt calls models through [OpenRouter](https://openrouter.ai). Create a key at [openrouter.ai/keys](https://openrouter.ai/keys). The same key serves the task model and System 1, the small classifier that routes each request.

```bash
# This terminal only:
export OPENROUTER_API_KEY="sk-or-v1-your-key"

# Or for every new terminal (bash; open a new terminal afterwards):
echo 'export OPENROUTER_API_KEY="sk-or-v1-your-key"' >> ~/.bashrc
```

| Setting | Required? | Where |
|---|---|---|
| `OPENROUTER_API_KEY` | Yes, for any live run | Environment variable, as above. Never put it in a file you commit. |
| The task model | No. The default is `nvidia/nemotron-3-super-120b-a12b:free` | `--model` (REPL, headless) or `create_worker("api", model=...)` (Python) |
| Everything else | No | [Reference: environment variables](../reference.md#environment-variables) |

**Credits.** Models whose name ends in `:free` cost nothing but are rate-limited, and OpenRouter can withdraw them. Other models, such as `openai/gpt-oss-120b`, need credit on your OpenRouter account.

## 6. Run a first task

This needs the key, network access and, for a paid model, credit. Run it from any folder: it writes a session folder there.

**Python API.** Save this as `first_task.py`:

```python
from pdl_taskmaster.api import Session, create_worker

worker = create_worker("api", model="nvidia/nemotron-3-super-120b-a12b:free")
with Session.open(worker, "pdlt-sessions/first-task", no_review=True) as session:
    result = session.send("Count the primes below 1000 and print the count.")
    print(result.text)
    print(result.stage, result.exit_status)
    if result.provenance:  # present when a result was published
        print(result.provenance["verification"]["level"])
```

```bash
python first_task.py
```

Expected: the answer (168), then `CLOSED_SUCCESS 0`, then `host_verified` (the host ran the program itself and reproduced the result). A free model can also end in `CLOSED_CANCELLED 1` (its repairs failed) or `CLOSED_UNVERIFIED 5` (it published something the host could not establish). Those are honest outcomes, not setup failures.

**Headless** (one task, then exit with a code your script can test):

```bash
printf '%s\n' "Count the primes below 1000 and print the count." | pdlt --non-interactive --new-session
echo $?
```

**REPL** (interactive):

```bash
pdlt --new-session
```

Type the task at the `>` prompt and press Enter. Type `/help` for the commands and `/quit` to leave. See [REPL and headless runs](../repl.md).

Sessions are kept in `runs/live-sessions/` inside a source checkout, otherwise in `~/.pdlt/runs/live-sessions/`.

## Use the MCP server from another agent

An MCP client starts the server itself. Give it the full path of the Python in your environment, for example:

```json
{
  "mcpServers": {
    "pdlt": {
      "command": "/home/you/pdlt-env/bin/python",
      "args": ["-m", "pdl_taskmaster.host.mcp_server"]
    }
  }
}
```

Find the path with `which python` while the environment is active. Tools, resources and flags: [MCP server](../mcp/EXTERNAL_TOOLS.md).

## Run programs in a container instead (optional)

Use this when Landlock is unavailable, or when you want stronger isolation. Install Docker or Podman, make sure your user can run it without `sudo`, and pull the image matching your Python version (for Python 3.12: `docker pull python:3.12-slim`). Then pass `--sandbox container`, or `export PDLT_SANDBOX=container`. The sandbox check in step 4 with `'container'` in place of `'auto'` prints `container 0 42`. CI (`sandbox.yml`) runs the confinement suite against this backend on Linux. `PDLT_CONTAINER_RUNTIME` and `PDLT_CONTAINER_IMAGE` choose the runtime and the image ([Sandbox guide](../SANDBOX.md#container-mode)).

To run without the OS sandbox, for diagnostics only, pass `--sandbox audit-only` or `export PDLT_SANDBOX=audit-only`: programs then run with the in-process audit hook and the resource limits only, and PDLt prints a warning. There is no `off` mode.

To choose the runtime or image: `PDLT_CONTAINER_RUNTIME` (default: `docker`, else `podman`) and `PDLT_CONTAINER_IMAGE` (default: `python:<your major.minor>-slim`).

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `The virtual environment was not created successfully because ensurepip is not available` | Install `python3-venv` (Debian, Ubuntu), then repeat step 2. |
| `pdlt: command not found` | The environment is not active in this terminal. Run the `source` line from step 2. |
| `SandboxNotConfined`, or `[warn] code execution unavailable` when the REPL starts | No Landlock: see step 4, or use the container backend. |
| A program fails opening a UDP or UNIX socket, or calling `fork` | Blocked on purpose: on Linux these are stopped by PDLt's audit hook (the kernel layer does not cover them). |
| Exit code 4, or `[harness-error]` on the error output | A provider or harness error, not a task result. See [Reference: when something fails](../reference.md#when-something-fails). |

## Next steps

- [Python API](../api.md): sessions, review gates, results, providers and run settings.
- [Extensions SDK](../extensions.md): your own task types, verifiers and model providers.
- [REPL and headless runs](../repl.md): every command, flag and exit code.
- [MCP server](../mcp/EXTERNAL_TOOLS.md): what other agents can call.
- [Sandbox guide](../SANDBOX.md): what confinement covers, and its known gaps.
