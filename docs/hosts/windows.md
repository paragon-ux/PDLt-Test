# Windows

This page sets PDLt up on Windows 10 or 11, from nothing to a first verified task. Every command is for **PowerShell**: open it from the Start menu ("Windows PowerShell" or "PowerShell"). Lines starting with `#` are comments; you do not need to type them.

**What it does here.** PDLt runs model-written programs inside an **AppContainer**, the confinement Windows itself uses for store apps. Nothing extra is installed for it.

**At the end you will have:** PDLt installed in a virtual environment, the `pdlt` command working, the sandbox confirmed, and one task run end to end.

## 1. Prerequisites

| Need | Detail |
|---|---|
| Windows 10 or 11 | Set up and tested on Windows 11; CI runs the suite on GitHub's `windows-latest` runners. |
| Python 3.10 to 3.14 | From [python.org](https://www.python.org/downloads/windows/). **Not the Microsoft Store build:** it cannot start the nested AppContainer, so PDLt would run no program. The python.org installer also installs the `py` launcher used below. |
| git | Only to install from source: [git-scm.com](https://git-scm.com/download/win). |
| An OpenRouter API key | Only for step 5. Steps 1 to 4 need none. |

**Check:**

```powershell
py --list                                          # the Python versions installed
py -3 -c "import sys; print(sys.version); print(sys.executable)"
```

The version must be 3.10 to 3.14. If the path printed contains `WindowsApps`, that is the Microsoft Store build: install Python from python.org and use that one.

## 2. Install

Pick one. Both create a virtual environment so PDLt does not touch your system Python.

**From PyPI** (a released version; 2.6.0 or later has the Python API and the extensions SDK). Run this in the folder where you want the environment, for example your home folder:

```powershell
cd $HOME
py -3 -m venv pdlt-env
.\pdlt-env\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install "pdl-taskmaster>=2.6.0"
```

**From source** (to run the test suite, the evaluation catalogue, or change the code):

```powershell
cd $HOME
git clone https://github.com/paragon-ux/PDLt-Test.git
cd PDLt-Test
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

After activation, your prompt starts with `(pdlt-env)` or `(.venv)`. Every later command on this page assumes that environment is active. In a new PowerShell window, run the `Activate.ps1` line again first.

**Check:**

```powershell
pdlt version
```

Expected: one line such as `pdl-taskmaster 2.6.0 (protocol specification: v2, manifest: C0-R4-1.0)`.

## 3. Verify offline

**From source:** run the offline test suite and the integrity gate from the `PDLt-Test` folder. No API key or network is used: models are scripted or replayed from recordings.

```powershell
python -m pytest -q -n auto
python -m pytest tests/test_harness_anti_overfitting.py -W error
```

Expected: the first ends with a line like `1321 passed, 42 skipped` (the numbers change as tests are added; skips are backends this machine does not have, such as Landlock). The second must report every test passed, with no warnings or skips. Any `failed` or `error` means the install is not sound.

**From PyPI:** the tests are not in the package. Run an empty headless session instead:

```powershell
"/quit" | pdlt --non-interactive --new-session --workspace-root "$env:TEMP\pdlt-check"
$LASTEXITCODE
```

Expected: it prints a short start-up banner, then `0`.

## 4. Check the sandbox

```powershell
python -c "from pdl_taskmaster.api import create_sandbox; s = create_sandbox('auto', label='setup-check', require_confined=True); r = s.run_code('print(6 * 7)'); print(s.backend_name, r.exit_code, r.stdout.strip()); s.close()"
```

Expected: `appcontainer 0 42`.

If it raises `SandboxNotConfined`, no OS-native sandbox is available and PDLt will run no program. On Windows the usual cause is the Microsoft Store Python (step 1). From source, the full escape suite is `python -m pytest tests/test_confinement.py -v`.

## 5. Configure a model

PDLt calls models through [OpenRouter](https://openrouter.ai). Create a key at [openrouter.ai/keys](https://openrouter.ai/keys). The same key serves the task model and System 1, the small classifier that routes each request.

```powershell
# This window only:
$env:OPENROUTER_API_KEY = "sk-or-v1-your-key"

# Or for every new window (open a new window afterwards):
setx OPENROUTER_API_KEY "sk-or-v1-your-key"
```

On Windows, when the current window does not have the key, PDLt also reads one saved for your user or the machine (as `setx` does), so a key saved once works in windows opened earlier too.

| Setting | Required? | Where |
|---|---|---|
| `OPENROUTER_API_KEY` | Yes, for any live run | Environment variable, as above. Never put it in a file you commit. |
| The task model | No. The default is `openai/gpt-oss-120b`, the model the defaults were measured on (L167); `nvidia/nemotron-3-super-120b-a12b:free` costs nothing | `--model` (REPL, headless) or `create_worker("api", model=...)` (Python) |
| Everything else | No | [Reference: environment variables](../reference.md#environment-variables) |

**Credits.** Models whose name ends in `:free` cost nothing but are rate-limited, and OpenRouter can withdraw them. Other models, such as the default `openai/gpt-oss-120b`, need credit on your OpenRouter account. The first task below names the free model, so it runs without credit.

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

```powershell
python first_task.py
```

Expected: the answer (168), then `CLOSED_SUCCESS 0`, then `host_verified` (the host ran the program itself and reproduced the result). A free model can also end in `CLOSED_CANCELLED 1` (its repairs failed) or `CLOSED_UNVERIFIED 5` (it published something the host could not establish). Those are honest outcomes, not setup failures.

**Headless** (one task, then exit with a code your script can test):

```powershell
"Count the primes below 1000 and print the count." | pdlt --non-interactive --new-session
$LASTEXITCODE
```

**REPL** (interactive):

```powershell
pdlt --new-session
```

Type the task at the `>` prompt and press Enter. Type `/help` for the commands and `/quit` to leave. See [REPL and headless runs](../repl.md).

Sessions are kept in `runs\live-sessions\` inside a source checkout, otherwise in `$HOME\.pdlt\runs\live-sessions\`.

## Use the MCP server from another agent

An MCP client starts the server itself. Give it the full path of the Python in your environment, for example:

```json
{
  "mcpServers": {
    "pdlt": {
      "command": "C:\\Users\\you\\pdlt-env\\Scripts\\python.exe",
      "args": ["-m", "pdl_taskmaster.host.mcp_server"]
    }
  }
}
```

Backslashes are doubled in JSON. Find the path with `(Get-Command python).Source` while the environment is active. Tools, resources and flags: [MCP server](../mcp/EXTERNAL_TOOLS.md).

## Run programs in a container instead (optional)

Install Docker Desktop, start it, and pull the image matching your Python version (for Python 3.12: `docker pull python:3.12-slim`). Then pass `--sandbox container`, or set `$env:PDLT_SANDBOX = "container"`. The sandbox check in step 4 with `'container'` in place of `'auto'` should print `container 0 42`. CI (`sandbox.yml`) tests the container backend on Linux only; on Windows 11 with Docker Desktop (Linux engine) the confinement suite passed locally (L135). The program runs on Linux in the container, so Windows paths and APIs are not its own. `PDLT_CONTAINER_RUNTIME` and `PDLT_CONTAINER_IMAGE` choose the runtime and the image ([Sandbox guide](../SANDBOX.md#container-mode)).

To run without the OS sandbox, for diagnostics only, pass `--sandbox audit-only` or set `$env:PDLT_SANDBOX = "audit-only"`: programs then run with the in-process audit hook and the resource limits only, and PDLt prints a warning. There is no `off` mode.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `Activate.ps1 cannot be loaded because running scripts is disabled on this system` | PowerShell's script policy. Run `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` once, or skip activation and call `.\pdlt-env\Scripts\python.exe` and `.\pdlt-env\Scripts\pdlt.exe` directly. |
| `pdlt : The term 'pdlt' is not recognized` | The environment is not active in this window. Run the `Activate.ps1` line from step 2. |
| `SandboxNotConfined`, or `[warn] code execution unavailable` when the REPL starts | No AppContainer. Use a python.org Python, not the Microsoft Store build (step 1). |
| Accented or non-Latin characters in a piped prompt arrive as `?` | Windows PowerShell 5.1 pipes text to programs as ASCII. Run `$OutputEncoding = [System.Text.Encoding]::UTF8` first, or pass the task with `--prompt-file task.txt` (a UTF-8 file). |
| A program cannot open `NUL` | A known AppContainer limit: programs cannot open the null device. Write to a file instead. |
| Exit code 4, or `[harness-error]` on the error output | A provider or harness error, not a task result. See [Reference: when something fails](../reference.md#when-something-fails). |

## Next steps

- [Python API](../api.md): sessions, review gates, results, providers and run settings.
- [Extensions SDK](../extensions.md): your own task types, verifiers and model providers.
- [REPL and headless runs](../repl.md): every command, flag and exit code.
- [MCP server](../mcp/EXTERNAL_TOOLS.md): what other agents can call.
- [Sandbox guide](../SANDBOX.md): what confinement covers, and its known gaps.
