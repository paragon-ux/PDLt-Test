# Catalogue Suite & Evaluation Methodology

The PDLt evaluation suite measures agentic reasoning, instruction fidelity, and structural integrity across **112 curated prompts** distributed across 16 challenging categories.

---

## The 16 Catalogue Categories

| # | Category | Key Challenge |
| :--- | :--- | :--- |
| `01` | **Combinatorial Search** | Backtracking, branch-and-bound, witness construction (e.g. Schur triples) |
| `02` | **Data Structures** | Custom heaps, red-black trees, memory layouts |
| `03` | **Systems Programming** | Memory allocators, virtual memory, process models |
| `04` | **Parsers & Compilers** | Recursive descent, AST transformations, bytecode generation |
| `05` | **Algorithm Design** | Dynamic programming, graph flow, divide-and-conquer |
| `06` | **Debugging & Repair** | Multi-file isolation, silent regressions, race conditions |
| `07` | **Refactoring & Design** | Architectural modularization, clean abstraction boundaries |
| `08` | **Specification Extraction** | Converting ambiguous natural language into formal requirements |
| `09` | **Adversarial & Injection** | Semantic prompt injection, jailbreaks, passive raw data containment |
| `10` | **Multi-Turn & Revision** | State preservation, incremental diffs, interactive revisions |
| `11` | **Cross-Domain Composition** | Combining disparate APIs, heterogeneous algorithmic concepts |
| `12` | **Domain Knowledge** | Specialized mathematical, cryptographic, or protocol specs |
| `13` | **Negative & Impossible** | Recognizing mathematically impossible constraints and refusing appropriately |
| `14` | **Formal Verification** | Invariant synthesis, pre/post-condition proofs, model checking |
| `15` | **Performance & Scale** | Algorithmic complexity bounds ($O(n \log n)$ vs $O(n^2)$) |
| `16` | **Logic & Reasoning** | Lateral riddles, deductive constraints, counterexample elimination |

---

## Verdicts & Ground-Truth Grading

Each execution produces an authoritative verdict and grade:

| Grade | Description |
| :--- | :--- |
| **PASS** | Reached expected terminal stage (`CLOSED_SUCCESS`) and output satisfies automated ground-truth solver. |
| **FAIL** | Failed to reach terminal stage, encountered runtime exception, or violated ground-truth solution. |
| **FALSE POSITIVE** | Reached `CLOSED_SUCCESS` but automated ground-truth grader detected incorrect deliverable. Strictly excluded from pass rate. |
| **MANUAL** | Correctness requires semantic human inspection (e.g. open-ended riddles, design tasks). |
| **UNGRADED / N/A** | Architectural categories evaluated on protocol adherence rather than single mathematical answers. |

---

## Anti-Overfitting Safeguards

To prevent benchmark overfitting:
1. **Zero Ground-Truth Leaks**: The execution harness (`src/pdl_taskmaster/`) contains zero prompt text, keyword regexes, or solutions.
2. **Automated Verification Probes**: `tests/test_harness_anti_overfitting.py` statically inspects the codebase to ensure no catalogue answers are hardcoded.
3. **Refusal Invariants**: Adversarial prompts (`09-01`) must execute benign tasks while containing injections in passive data; impossible prompts (`13-01`) must identify contradictions without spurious solver loops.
