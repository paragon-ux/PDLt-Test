# Get started

Setting PDLt up takes five steps. Each step ends with a check, so you, or an agent doing the setup, can tell it worked before going on. Only the last step calls a model; the others need no API key and no network beyond the install itself.

1. **Install** PDLt in a Python virtual environment.
2. **Verify offline**: the version command, and the test suite if you installed from source.
3. **Check the sandbox**: PDLt runs model-written programs only under the operating system's own confinement. If it is not available, PDLt runs no program at all.
4. **Configure a model**: one OpenRouter API key.
5. **Run a first task** through the Python API, the REPL or a headless command.

## Choose your host

The commands and the sandbox differ by operating system, so each one has its own page with every step written out for it. Follow only the page for your machine.

| Host | Sandbox backend | Shell used on the page | Tested in CI | Page |
|---|---|---|---|---|
| **Windows** 10 or 11 | AppContainer (built into Windows) | PowerShell | Full offline suite and confinement suite, Python 3.10 to 3.14 | [Windows](hosts/windows.md) |
| **Linux** (kernel 5.13 or later) | Landlock (built into the kernel) | bash | Full offline suite and confinement suite, including the container backend, Python 3.10 to 3.14 | [Linux](hosts/linux.md) |
| **macOS** | Seatbelt (`sandbox-exec`, built into macOS) | zsh or bash | Confinement and sandbox tests only, Python 3.10 to 3.14 | [macOS](hosts/macos.md) |

On any of them you can run programs in a Docker or Podman container instead of the native backend (`--sandbox container`). That is a sandbox mode, not a separate host: it is described on each host page.

## What you have at the end

- PDLt installed, with the `pdlt` command on your path.
- A confirmed sandbox: a test program ran confined and printed `42`.
- A first task run end to end, with its result, its exit code and its provenance (how far the host could check the result).

## After setup

| To | Read |
|---|---|
| Run tasks from your own Python code | [Python API](api.md) |
| Add your own task types, verifiers or model providers | [Extensions SDK](extensions.md) |
| Work interactively, or script PDLt from a shell | [REPL and headless runs](repl.md) |
| Let another agent use PDLt's sandbox and results | [MCP server](mcp/EXTERNAL_TOOLS.md) |
| Look up an environment variable, a file location or an exit code | [Reference](reference.md) |
| Choose models and providers | [Providers and models](providers.md) |
