## SUPPLIED TASK INPUT
Nodes: 0 through 49
Edges: Every node i is connected to node (i+1) mod 50, node (i+7) mod 50, and node (i+13) mod 50.

This is a regular graph with 150 edges. Minimum vertex cover is NP-hard. You must find the provably optimal solution, not an approximation.


## EXECUTION BRIEF (entity-dense; drafted prior to execution)
Construct the 50-node graph with edges (i, (i+1)%50), (i, (i+7)%50), (i, (i+13)%50). Formulate an integer linear program: binary variable x_v for each vertex v, minimize sum x_v subject to x_u + x_v >= 1 for every edge (u,v). Solve the ILP with the host's exact solver to obtain the optimal vertex cover set. Verify optimality by checking that the solution satisfies all edge constraints and that the objective value cannot be lowered. Emit the resulting set of vertices as the minimum vertex cover.
CRITICAL VERBATIM ENTITIES (each MUST appear verbatim in the deliverable; the host checks this mechanically):


DELIVERY FORMAT: file sections MUST be headed exactly by their marker lines (e.g. a line reading exactly '### cnf.py' immediately followed by that file's code).CONFIRMED REQUIREMENTS (mechanically derived; reconcile EVERY ID):
R1: COMPUTE the exact minimum vertex cover of the graph
R2: RETURN the set of vertices that forms a minimum vertex cover
R3: ENSURE the solution is provably optimal and not an approximation

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
