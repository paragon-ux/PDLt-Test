# Getting Started

This guide walks you through installation, running offline tests, launching the interactive REPL, and executing automated catalogue evaluation.

---

## Installation

PDLt requires Python 3.10 to 3.14.

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Clone the repository
git clone https://github.com/paragon-ux/PDLt-Test.git
cd PDLt-Test

# Install in editable mode with development & test dependencies
pip install -e ".[test]"
```

---

## Offline Test Suite

Before running live models, verify that the offline test suite and harness anti-overfitting gates pass 100%:

```bash
pytest -q
```

This verifies:
- 85+ formal output contract schemas
- 16+ harness anti-overfitting tests
- Sandbox confinement barriers and environment allowlists

---

## Interactive REPL

Set your OpenRouter API key:

=== "Linux / macOS"
    ```bash
    export OPENROUTER_API_KEY="sk-or-v1-..."
    ```

=== "Windows (PowerShell)"
    ```powershell
    $env:OPENROUTER_API_KEY = "sk-or-v1-..."
    ```

Launch the interactive REPL:

```bash
pdlt --new-session --dev
```

### REPL Commands & Workflow

In a standard session, the harness guides interaction through deterministic review gates:

```text
USER> Write a Python function to compute the Collatz stopping time.
ASSISTANT> Prompt Pseudocode:
   PARSE input positive integer n
   ITERATE: if even n/2, if odd 3n+1 until n == 1
   COUNT steps and RETURN
Confirm or correct this interpretation.
```

- `/confirm`: Approves pseudocode interpretation or plan.
- `/revise <feedback>`: Feeds specific revisions to the model to update the artifact.
- `/fast on|off`: Enables fast mode (automatically confirms when no host lint findings exist).
- `/stop` or `/cancel`: Terminates the active session safely.
- `/resume <session-id>`: Restores a prior session and displays the unconfirmed gate.

---

## Evaluation Runner & Local Viewer

Execute prompts across the 16-category catalogue:

```bash
# Validate manifest and list prompts (dry run)
python run_catalogue.py --dry-run

# Run a specific prompt
python run_catalogue.py --prompt-id 06-04

# Run pure sandboxed control baseline (raw unharnessed completions)
python run_catalogue.py --route control --prompt-id 01-01 --theme bright

# Sequential Five-Route Parity Sweep (Control + Arms 1-4), one route after another
M="--model openai/gpt-oss-120b --reasoning low --timeout 300"
python run_catalogue.py $M --route control
python run_catalogue.py $M --route unconfirmed
python run_catalogue.py $M --route unconfirmed --draft-execute
python run_catalogue.py $M --route confirmed
python run_catalogue.py $M --route confirmed --draft-execute

# Build the comparison tables from the finished runs
python experiments/five_arm_report.py --md report.md
```

Tier D1 (the sandbox repair loop) is on by default for the four harness routes; add `--no-tier-d1` to turn it off. It does not apply to `--route control`. A run from a dirty working tree is refused unless you pass `--allow-dirty`.


### Local Web Viewer

PDLt includes a localhost read-only browser viewer for inspecting sessions, scoreboards, and ground-truth artifacts:

```bash
python -m viewer
```
Opens `http://127.0.0.1:8090` in your default browser.
