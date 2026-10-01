CONFIRMED REQUIREMENTS (mechanically derived; reconcile EVERY ID):
R1: OPERATIVE TASK ENTITIES:
R2: - 3
R3: - 34
R4: - 7
R5: - 12
R6: - 5
R7: - 26
R8: - 11
R9: - 8
R10: - 15
R11: - 2
R12: - 19
R13: - 21
R14: - 40
R15: READ the set S = {3, 34, 7, 12, 5, 26, 11, 8, 15, 2, 19, 21}
R16: READ the target sum T = 40
R17: APPLY a backtracking algorithm that explores the full search tree to FIND all subsets of S whose elements sum exactly to T
R18: FOR each solution EMIT the subset and VERIFY that its sum equals T
R19: REPORT the total number of solutions found

The response MUST end with a fenced ```json block containing the Result IR object, exactly this shape:
{"files": [{"filename": "<name>.py", "satisfies": ["R<n>"], "evidence": {"path": "<workspace-relative path>", "section": "<verbatim section marker, optional>"}}], "reconciliation": [{"requirement": "R<n>", "status": "satisfied|partial|open", "evidence": {"path": "...", "section": "...", "observed": "<verbatim quote from the cited artifact>"}}], "open_defects": [{"id": "D<n>", "description": "<defect>", "evidence": {"path": "...", "observed": "<verbatim quote>"}}]}
Evidence rules: the path "execution://body" refers to THIS response's own deliverable text (use it for code and claims that exist only in this response); any other path MUST be one of the AVAILABLE EVIDENCE PATHS listed below; every "observed" string MUST be copied verbatim from the cited artifact; every requirement ID MUST appear in "reconciliation" exactly once; do not invent paths, sections, quotes, or requirement IDs; the host mechanically validates every citation and rejects fabrication.
AVAILABLE EVIDENCE PATHS: - execution://body
- execution://witness

WITNESS REQUIREMENT (ADR-0013 / ADR-0015): Because this task requires verified execution, your Result IR MUST include a 'witness' field certifying any result it claims:
- If a solution exists: {"polarity": "positive", "evidence": {"path": "execution://witness"}, "data": {<the concrete result, keyed by name>}}
- If no solution exists: {"polarity": "negative", "evidence": {"path": "execution://witness"}, "basis": "proof", "argument": "<the impossibility argument>"} or, for an exhausted search, {"polarity": "negative", "basis": "search", "search_exhausted": true, "nodes_explored": <states explored>, "method": "<method>"} printed as a WITNESS line by the program that ran the search
- If the result could not be obtained: emit no witness; mark each unmet requirement "open" in 'reconciliation' and record the reason in 'open_defects'.

WITNESS CERTIFICATION: When the deliverable includes code, the host sandbox executes it. Print exactly one line `WITNESS: <json>` to stdout; the host-reproduced witness replaces any witness asserted in the Result IR. A witness the host could not reproduce is reported as provisional.
