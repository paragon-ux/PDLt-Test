"""L115 feasibility, step 1 (live, free): tests written from the request alone, before and without any solution.
Question: can tests written from the request text separate recorded false successes from recorded passes?
Usage: l115_write_tests.py <repo> <out_dir> <model> <samples>. Prints status only; never the key."""
import json
import sys
import time
from pathlib import Path

repo, out_dir, model, samples = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], int(sys.argv[4])
sys.path.insert(0, str(repo / "src"))
from pdl_taskmaster.providers.api_worker import ApiWorker  # noqa: E402

PROMPTS = {"04-02": "04_parsers_and_compilers/json_streaming_parser.txt",
           "04-03": "04_parsers_and_compilers/regex_to_nfa_thompson.txt"}
INSTRUCTIONS = """Write a Python test module for the programming request below. Do not write a solution.
The tests check only behaviour the request states: the interface it names (use exactly those names), the examples it gives, and properties it states explicitly.
Each test is a function named test_<what_it_checks> that takes no arguments and uses assert with a message.
The functions and classes under test are already defined in the module's namespace; do not define or import them.
Import only the standard library. Where the request leaves something open, do not test it.
Return only the Python module, with no prose and no code fence."""

worker = ApiWorker(model=model, repo_root=repo)
key = worker._resolve_api_key()
out_dir.mkdir(parents=True, exist_ok=True)
for prompt_id, rel in PROMPTS.items():
    request = (repo / "prompts" / rel).read_text(encoding="utf-8-sig")
    for n in range(1, samples + 1):
        body = {"model": model, "instructions": INSTRUCTIONS, "input": "REQUEST:\n" + request,
                "max_output_tokens": 8192}
        started = time.perf_counter()
        data = worker._send_json_with_retries(worker._responses_request(body, key), time.monotonic() + 300)
        text = worker._extract_output_text(data)
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        path = out_dir / f"{prompt_id}-s{n}.py"
        path.write_text(text, encoding="utf-8")
        print(f"{prompt_id} sample {n}: {len(text)} chars, {text.count('def test_')} tests, "
              f"{time.perf_counter() - started:.0f}s", flush=True)
