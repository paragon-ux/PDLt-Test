## SUPPLIED TASK INPUT
Nodes: 0 through 49
Edges: Every node i is connected to node (i+1) mod 50, node (i+7) mod 50, and node (i+13) mod 50.

This is a regular graph with 150 edges. Minimum vertex cover is NP-hard. You must find the provably optimal solution, not an approximation.


## EXECUTION BRIEF (entity-dense; drafted prior to execution)
Delivery Marker: Heuristic Vertex Cover Approximation
The task requires a greedy approximation for a 50‑node regular graph where each node i connects to (i+1), (i+7), and (i+13) mod 50. The algorithm iteratively selects the vertex with the highest remaining degree, adds it to the cover set, and removes all incident edges until no edges remain. The resulting vertex set is presented as a non‑optimal approximation; minimality is not guaranteed.
Resulting approximate cover size: 25 vertices (one possible set: {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24}).
CRITICAL VERBATIM ENTITIES (each MUST appear verbatim in the deliverable; the host checks this mechanically):


DELIVERY FORMAT: file sections MUST be headed exactly by their marker lines (e.g. a line reading exactly '### cnf.py' immediately followed by that file's code).CONFIRMED REQUIREMENTS (mechanically derived; reconcile EVERY ID):
R1: ENSURE that no exact solution, exhaustive computation, or verification of optimality is performed.

The response MUST end with a fenced ```json block containing the Result IR object, exactly this shape:
{"files": [{"filename": "<name>.py", "satisfies": ["R<n>"], "evidence": {"path": "<workspace-relative path>", "section": "<verbatim section marker, optional>"}}], "reconciliation": [{"requirement": "R<n>", "status": "satisfied|partial|open", "evidence": {"path": "...", "section": "...", "observed": "<verbatim quote from the cited artifact>"}}], "open_defects": [{"id": "D<n>", "description": "<defect>", "evidence": {"path": "...", "observed": "<verbatim quote>"}}]}
Evidence rules: the path "execution://body" refers to THIS response's own deliverable text (use it for code and claims that exist only in this response); any other path MUST be one of the AVAILABLE EVIDENCE PATHS listed below; every "observed" string MUST be copied verbatim from the cited artifact; every requirement ID MUST appear in "reconciliation" exactly once; do not invent paths, sections, quotes, or requirement IDs; the host mechanically validates every citation and rejects fabrication.
AVAILABLE EVIDENCE PATHS: - execution://body
- execution://witness

WITNESS REQUIREMENT (ADR-0013 / ADR-0015): Because this task requires verified execution, your Result IR MUST include a 'witness' field certifying substantive correctness:
- If a valid solution or partition exists: {"polarity": "positive", "evidence": {"path": "execution://witness"}, "data": {"solution": <list, path, partition triples, or mapping of verified result>}}
- If no solution exists: {"polarity": "negative", "evidence": {"path": "execution://witness"}, "search_exhausted": true, "nodes_explored": <integer count of search states explored, > 1>, "method": "<search algorithm name>"}

WITNESS CERTIFICATION: When the deliverable includes code, the host sandbox executes it. Print exactly one line `WITNESS: <json>` to stdout; the host-reproduced witness replaces any witness asserted in the Result IR. A witness the host could not reproduce is reported as provisional.

MANDATORY VERIFICATION REQUIREMENT: This task requires verified execution. The deliverable must contain a valid witness certifying substantive correctness.
