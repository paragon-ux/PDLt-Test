"""Anti-Overfitting and Benchmark Integrity Guardrail Unit Tests (GUARD-01 to GUARD-05).

Verifies that the PDL-Taskmaster harness maintains absolute neutrality and does not
harbor benchmark-gaming heuristics, prompt-targeted token hacks, or synthetic solver injections.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_guard01_no_synthetic_carried_approach_injection():
    """GUARD-01: session_engine._draft_plan must NOT inject synthetic carried approaches."""
    session_engine_file = ROOT / "src" / "pdl_taskmaster" / "runtime" / "session_engine.py"
    text = session_engine_file.read_text(encoding="utf-8")

    # Locate _draft_plan definition
    assert "def _draft_plan(" in text
    draft_plan_body = text.split("def _draft_plan(")[1].split("def ")[0]

    # Must NOT inject synthetic carried approach strings
    prohibited_snippets = [
        "search for the partition triples",
        "Algorithm X",
        "DLX",
        "backtracking solver script",
        "subset sum solver script",
    ]
    for snippet in prohibited_snippets:
        assert snippet not in draft_plan_body, (
            f"GUARD-01 VIOLATION: Found synthetic solver injection '{snippet}' in _draft_plan."
        )


def test_guard02_problem_class_clean_patterns():
    """GUARD-02: problem_class must not target conversational, riddle, or family logic keywords."""
    problem_class_file = ROOT / "src" / "pdl_taskmaster" / "providers" / "sys1" / "recipes" / "problem_class.py"
    text = problem_class_file.read_text(encoding="utf-8")

    # Combinatorial regex patterns must not include conversational logic/riddle tokens
    prohibited_tokens = [
        "sisters?",
        "brothers?",
        "how\\s+many\\s+sisters",
        "family\\s+relationship",
        "riddle",
    ]
    for token in prohibited_tokens:
        assert token not in text, (
            f"GUARD-02 VIOLATION: Found benchmark-targeted token '{token}' in problem_class.py."
        )


def test_guard02_activation_route_no_hardcoded_refusal_literals():
    """GUARD-02: activation_route refusal strings must not hardcode benchmark entities."""
    activation_route_file = ROOT / "src" / "pdl_taskmaster" / "providers" / "sys1" / "recipes" / "activation_route.py"
    text = activation_route_file.read_text(encoding="utf-8")

    # Refusal string must dynamically format matched package name rather than hardcoding ('frostbitedb')
    assert "('frostbitedb')" not in text, (
        "GUARD-02 VIOLATION: Found hardcoded refusal entity ('frostbitedb') in activation_route.py."
    )


_TEXT_SUFFIXES = {".md", ".json", ".txt", ".py", ".yaml", ".yml"}
# Both manifest copies: the repository's and the one bundled in the package (the
# NormativeStore fallback). Each lists paths relative to its own base directory.
_MANIFEST_BASES = (ROOT, ROOT / "src" / "pdl_taskmaster")


def _normalized_bytes(path: Path) -> bytes:
    """File bytes with CRLF folded to LF for text files, so a Windows checkout
    (core.autocrlf) hashes like the LF original."""
    raw = path.read_bytes()
    return raw.replace(b"\r\n", b"\n") if path.suffix in _TEXT_SUFFIXES else raw


def _manifest_divergences(base: Path) -> list[str]:
    manifest = json.loads((base / "contracts" / "CONTRACT_MANIFEST.json").read_text(encoding="utf-8"))
    mismatches = []
    for entry in manifest.get("files", []):
        file_path = base / entry["path"]
        assert file_path.is_file(), f"Manifest references missing file: {entry['path']}"
        actual_sha = hashlib.sha256(_normalized_bytes(file_path)).hexdigest()
        if entry["sha256"] != actual_sha:
            mismatches.append(f"{entry['path']}: expected {entry['sha256'][:10]} got {actual_sha[:10]}")
    return mismatches


@pytest.mark.parametrize("base", _MANIFEST_BASES, ids=["repository", "bundled"])
def test_guard05_contract_manifest_sha256_synchronized(base):
    """GUARD-05: CONTRACT_MANIFEST.json must have 0 SHA-256 hash divergences."""
    assert (base / "contracts" / "CONTRACT_MANIFEST.json").is_file()
    mismatches = _manifest_divergences(base)
    assert not mismatches, f"CONTRACT_MANIFEST.json hash divergences found:\n" + "\n".join(mismatches)


def test_guard05_bundled_contract_manifest_matches_the_repository_copy():
    repository, bundled = (base / "contracts" / "CONTRACT_MANIFEST.json" for base in _MANIFEST_BASES)
    assert _normalized_bytes(repository) == _normalized_bytes(bundled)


def test_plan_soundness_accepts_pure_deduction_plan():
    """GUARD-03: Plan soundness must accept pure analytical/deductive plans without code."""
    from pdl_taskmaster.verification.plan_soundness import validate_plan_soundness

    analytical_plan = (
        "ANALYZE the sibling relationships for Alice and her family\n"
        "DEDUCE the total number of female siblings including Alice\n"
        "COMPUTE the number of sisters that each brother has\n"
        "EMIT the result in terms of M"
    )
    # The lint is task-neutral: identical verdict for every task class (GUARD-03/04)
    for flag in (False, True):
        result = validate_plan_soundness(analytical_plan, requires_verified_execution=flag)
        assert result.valid, (flag, result.violations)
        assert len(result.violations) == 0


def test_guard_no_mrv_or_algorithmic_coaching_in_harness():
    """GUARD-04: Harness prompts and runtime must NOT spoon-feed MRV or specific algorithms."""
    targets = [
        ROOT / "src" / "pdl_taskmaster" / "runtime" / "session_engine.py",
        ROOT / "src" / "pdl_taskmaster" / "runtime" / "result_ir.py",
        ROOT / "src" / "pdl_taskmaster" / "providers" / "api_worker.py",
        ROOT / "src" / "pdl_taskmaster" / "verification" / "plan_soundness.py",
        ROOT / "src" / "pdl_taskmaster" / "verification" / "sandbox.py",
    ]
    for path in targets:
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"\bMRV\b", text, re.I), (
            f"GUARD-04 VIOLATION: Found algorithmic coaching 'MRV' in {path.name}"
        )
        assert "Alice has M sisters" not in text, (
            f"GUARD-04 VIOLATION: Found prompt-specific answer in {path.name}"
        )


def test_guard_no_witness_fabrication_or_regex_scraping():
    """GUARD-03: Verifiers must NOT regex-scrape deliverable text or invent fake exploration numbers."""
    from pdl_taskmaster.verification.checkers.base import ProblemDomain
    from pdl_taskmaster.verification.output_verifier import OutputVerifier

    # No problem-specific checker ships in the harness plane (GUARD-02).
    assert OutputVerifier()._checkers == {}
    assert [d.value for d in ProblemDomain] == ["general"]

    session_engine_file = ROOT / "src" / "pdl_taskmaster" / "runtime" / "session_engine.py"
    se_text = session_engine_file.read_text(encoding="utf-8")
    assert '"nodes_explored": 100' not in se_text, (
        "GUARD-03 VIOLATION: Found fabricated negative witness numbers in session_engine.py"
    )


def test_guard_no_benchmark_probe_interceptions():
    """GUARD-02: System 1 must NOT hardcode benchmark trap packages."""
    route_file = ROOT / "src" / "pdl_taskmaster" / "providers" / "sys1" / "recipes" / "activation_route.py"
    route_text = route_file.read_text(encoding="utf-8")
    assert "frostbite" not in route_text.lower(), (
        "GUARD-02 VIOLATION: Found hardcoded benchmark probe package 'frostbite' in activation_route.py"
    )


def _manifest_stems() -> list[str]:
    manifest = ROOT / "prompts" / "CATALOGUE_MANIFEST.jsonl"
    stems = []
    for line in manifest.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            stems.append(Path(json.loads(line)["file"]).stem.lower())
    return stems


# Hyphenated manifest tags that name protocol concepts, not problem classes.
_PROTOCOL_TAGS = {
    "pdl-05", "utf-8", "code-fence", "cross-turn", "fielded-schema", "knowledge-cutoff",
    "negative-witness", "plan-review", "prompt-review", "self-reference", "state-machine",
    "system-prompt",
}


def _manifest_tag_patterns() -> list[str]:
    """Problem-class vocabulary derived from the manifest: every multi-word tag
    (exact-cover, subset-sum, bin-packing, ...) matched across space/underscore/hyphen."""
    manifest = ROOT / "prompts" / "CATALOGUE_MANIFEST.jsonl"
    tags: set[str] = set()
    for line in manifest.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            tags.update(t.lower() for t in json.loads(line)["tags"] if "-" in t)
    return [
        r"\b" + r"[\s_-]".join(re.escape(part) for part in tag.split("-")) + r"\b"
        for tag in sorted(tags - _PROTOCOL_TAGS)
    ]


def test_benchmark_contamination_scan():
    """GUARD-01/02/04/05: harness plane has ZERO benchmark IDs, prompt stems, or problem vocabulary."""
    src_dir = ROOT / "src" / "pdl_taskmaster"
    prompt_id_pattern = re.compile(r"\b(0[1-9]|1[0-5])-(0[1-7])\b")
    word_tokens = [
        r"frostbite", r"schur", r"\bdlx\b", r"dancing\s+link", r"algorithm\s+x", r"backtrack",
        r"\bmrv\b", r"nobel", r"hamiltonian", r"palindrome", r"wheel\s+graph", r"alice\s+has",
        r"catalogue_manifest", r"prompts/", r"solutions/", r"\btriples?\b",
        r"\bpartition(?:s|ed|ing)?\b(?!\()",
    ]
    tag_patterns = _manifest_tag_patterns()
    assert len(tag_patterns) > 50
    stem_tokens = _manifest_stems()
    assert len(stem_tokens) == 105

    violations: list[str] = []
    files = list(src_dir.rglob("*.py")) + list(src_dir.rglob("*.txt"))
    assert files
    for path in files:
        content = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT)
        prompt_match = prompt_id_pattern.search(content)
        if prompt_match:
            violations.append(f"{rel}: contains benchmark prompt ID '{prompt_match.group(0)}'")
        lower = content.lower()
        for pat in word_tokens:
            if re.search(pat, lower):
                violations.append(f"{rel}: contains benchmark/algorithm vocabulary /{pat}/")
        for pat in tag_patterns:
            if re.search(pat, lower):
                violations.append(f"{rel}: contains manifest problem-class tag /{pat}/")
        for stem in stem_tokens:
            if stem in lower:
                violations.append(f"{rel}: contains benchmark prompt stem '{stem}'")

    assert not violations, (
        "GUARD VIOLATION: Benchmark contamination found in production source:\n"
        + "\n".join(violations)
    )


def test_carried_sources_never_receive_feedback():
    """GUARD-01: CARRIED_APPROACH_SOURCES is always exactly the user-originated `carried` list."""
    text = (ROOT / "src" / "pdl_taskmaster" / "runtime" / "session_engine.py").read_text(encoding="utf-8")
    body = text.split("def _draft_plan(")[1].split("\n    def ")[0]
    values = re.findall(r'"CARRIED_APPROACH_SOURCES":\s*([^,\n]+),', body)
    assert values, "expected CARRIED_APPROACH_SOURCES bindings in _draft_plan"
    assert all(v.strip() == "carried" for v in values), values
    assert "carried_feedback" not in text
    assert "Operational approach requirement" not in text


def test_worker_guidance_does_not_mandate_code_or_algorithms():
    """GUARD-04: worker guidance never mandates a solver script or names a method."""
    text = (ROOT / "src" / "pdl_taskmaster" / "providers" / "api_worker.py").read_text(encoding="utf-8")
    assert "MUST contain the complete, executable Python" not in text
    assert "specify the algorithm, data structures" not in text
    for banned in ("solver script", "backtracking", "dynamic programming"):
        assert banned not in text.lower(), banned


def test_verifier_never_infers_domain_from_text():
    """GUARD-02: problem text is never inspected for domain vocabulary."""
    from pdl_taskmaster.verification.output_verifier import OutputVerifier

    verifier = OutputVerifier()
    for text in ("Partition the numbers into triples", "find an exact cover", "subset sum target"):
        assert verifier.detect_domain(text) is None


def test_routing_recipes_have_no_pattern_matching():
    """GUARD-02: System 1 routes environment recipe state; recipes never match keywords or dates."""
    recipes = ROOT / "src" / "pdl_taskmaster" / "providers" / "sys1" / "recipes"
    for name in ("activation_route.py", "problem_class.py"):
        text = (recipes / name).read_text(encoding="utf-8")
        assert "re.compile" not in text, name
        assert "import re" not in text, name
        assert "classify_text_deterministic" not in text, name
    worker = (ROOT / "src" / "pdl_taskmaster" / "providers" / "api_worker.py").read_text(encoding="utf-8")
    assert "classify_text_deterministic" not in worker
