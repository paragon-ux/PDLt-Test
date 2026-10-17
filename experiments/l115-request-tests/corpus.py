"""Index the recorded 04-02 and 04-03 runs: grade, closure, and the published deliverable. Reads files only."""
import json
import sys
from collections import Counter
from pathlib import Path

root = Path(sys.argv[1])
rows = []
for result in root.glob("run-*/results/04-0[23]_*/result.json"):
    try:
        data = json.loads(result.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        continue
    current = list(result.parent.glob("session/**/stages/50_execution/output/current.md"))
    rows.append({"run": result.parents[2].name, "prompt": data.get("id"), "verdict": data.get("verdict"),
                 "grade": (data.get("ground_truth_grade") or {}).get("grade") if isinstance(data.get("ground_truth_grade"), dict) else data.get("ground_truth_grade"), "grade_raw": data.get("ground_truth_grade"), "exit": data.get("exit_code"),
                 "deliverable": str(current[0]) if len(current) == 1 else None, "n_current": len(current)})
print(len(rows), "results")
print(Counter((r["prompt"], r["verdict"], r["grade"]) for r in rows).most_common())
print("with one deliverable:", sum(1 for r in rows if r["deliverable"]))
out = Path(sys.argv[2])
out.write_text(json.dumps(rows, indent=1), encoding="utf-8")
