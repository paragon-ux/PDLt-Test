CONFIRMED REQUIREMENTS (mechanically derived; reconcile EVERY ID):
R1: READ variables x, y, z and constraints C1, C2, C3, C4, C5, C6.
R2: USE entity x
R3: USE entity y
R4: USE entity z
R5: USE entity C1
R6: USE entity C2
R7: USE entity C3
R8: USE entity C4
R9: USE entity C5
R10: USE entity C6
R11: EVALUATE all assignments of values from {1, 2, 3} to x, y, z that satisfy every constraint.
R12: IF any assignments satisfy all constraints THEN LIST each satisfying assignment.
R13: ELSE PROVIDE a brief explanation of the conflicting constraints that prevent any solution.

The response MUST end with a fenced ```json block containing the Result IR object, exactly this shape:
{"files": [{"filename": "<name>.py", "satisfies": ["R<n>"], "evidence": {"path": "<workspace-relative path>", "section": "<verbatim section marker, optional>"}}], "reconciliation": [{"requirement": "R<n>", "status": "satisfied|partial|open", "evidence": {"path": "...", "section": "...", "observed": "<verbatim quote from the cited artifact>"}}], "open_defects": [{"id": "D<n>", "description": "<defect>", "evidence": {"path": "...", "observed": "<verbatim quote>"}}]}
Evidence rules: the path "execution://body" refers to THIS response's own deliverable text (use it for code and claims that exist only in this response); any other path MUST be one of the AVAILABLE EVIDENCE PATHS listed below; every "observed" string MUST be copied verbatim from the cited artifact; every requirement ID MUST appear in "reconciliation" exactly once; do not invent paths, sections, quotes, or requirement IDs; the host mechanically validates every citation and rejects fabrication.
AVAILABLE EVIDENCE PATHS: - execution://body
- execution://witness

WITNESS REQUIREMENT (ADR-0013 / ADR-0015): Because this task requires verified execution, your Result IR MUST include a 'witness' field certifying any result it claims:
- If a solution exists: {"polarity": "positive", "evidence": {"path": "execution://witness"}, "data": {<the concrete result, keyed by name>}}
- If no solution exists: {"polarity": "negative", "evidence": {"path": "execution://witness"}, "basis": "proof", "argument": "<the impossibility argument>"} or, for an exhausted search, {"polarity": "negative", "basis": "search", "search_exhausted": true, "nodes_explored": <states explored>, "method": "<method>"}
- If the result could not be obtained: emit no witness; mark each unmet requirement "open" in 'reconciliation' and record the reason in 'open_defects'.

WITNESS CERTIFICATION: When the deliverable includes code, the host sandbox executes it. Print exactly one line `WITNESS: <json>` to stdout; the host-reproduced witness replaces any witness asserted in the Result IR. A witness the host could not reproduce is reported as provisional.
