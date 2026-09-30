CONFIRMED REQUIREMENTS (mechanically derived; reconcile EVERY ID):
R1: REQUEST the exact minimum vertex cover of the specified 50-node regular graph where each node i connects to (i+1) mod 50, (i+7) mod 50, and (i+13) mod 50.
R2: NOTE that computing a minimum vertex cover is NP‑hard and that a provably optimal solution may be computationally infeasible for this instance.
R3: ACKNOWLEDGE the computational infeasibility and, if optimal solution cannot be obtained, PROVIDE either a best‑effort heuristic result clearly labeled as NON‑OPTIMAL or a reduced‑size version of the problem with an explanation of the reduction.

The response MUST end with a fenced ```json block containing the Result IR object, exactly this shape:
{"files": [{"filename": "<name>.py", "satisfies": ["R<n>"], "evidence": {"path": "<workspace-relative path>", "section": "<verbatim section marker, optional>"}}], "reconciliation": [{"requirement": "R<n>", "status": "satisfied|partial|open", "evidence": {"path": "...", "section": "...", "observed": "<verbatim quote from the cited artifact>"}}], "open_defects": [{"id": "D<n>", "description": "<defect>", "evidence": {"path": "...", "observed": "<verbatim quote>"}}]}
Evidence rules: the path "execution://body" refers to THIS response's own deliverable text (use it for code and claims that exist only in this response); any other path MUST be one of the AVAILABLE EVIDENCE PATHS listed below; every "observed" string MUST be copied verbatim from the cited artifact; every requirement ID MUST appear in "reconciliation" exactly once; do not invent paths, sections, quotes, or requirement IDs; the host mechanically validates every citation and rejects fabrication.
AVAILABLE EVIDENCE PATHS: - execution://body
- execution://witness

WITNESS REQUIREMENT (ADR-0013 / ADR-0015): Because this task requires verified execution, your Result IR MUST include a 'witness' field certifying substantive correctness:
- If a solution exists: {"polarity": "positive", "evidence": {"path": "execution://witness"}, "data": {<the concrete result, keyed by name>}}
- If no solution exists: {"polarity": "negative", "evidence": {"path": "execution://witness"}, "basis": "proof", "argument": "<the impossibility argument>"} or, for an exhausted search, {"polarity": "negative", "basis": "search", "search_exhausted": true, "nodes_explored": <states explored>, "method": "<method>"}

WITNESS CERTIFICATION: When the deliverable includes code, the host sandbox executes it. Print exactly one line `WITNESS: <json>` to stdout; the host-reproduced witness replaces any witness asserted in the Result IR. A witness the host could not reproduce is reported as provisional.
