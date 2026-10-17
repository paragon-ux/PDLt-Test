"""L115 option 1 report: signature-bound request tests, one module per recorded deliverable, grouped by prompt and
grade. A failure is 'interface' when the test could not reach the deliverable through the names it was given,
'behaviour' otherwise. Usage: report_bound.py <results.json>"""
import json
import re
import sys
from collections import Counter, defaultdict

INTERFACE = re.compile(r"NameError|AttributeError|TypeError|ImportError|ModuleNotFoundError|not defined|"
                       r"has no attribute|positional argument|unexpected keyword")
results = json.load(open(sys.argv[1], encoding="utf-8"))
table = defaultdict(lambda: Counter())
failing_tests_on_passes = Counter()
for r in results:
    row = table[(r["prompt"], r["grade"])]
    row["n"] += 1
    report = r["report"]
    if report.get("missing"):
        row["no tests written"] += 1
        continue
    if "incomplete" in report or "module_error" in report or not report.get("tests"):
        row["no runnable tests"] += 1
        continue
    kinds = Counter("interface" if INTERFACE.search(v) else "behaviour"
                    for v in report["tests"].values() if v != "ok")
    row["any failure"] += bool(kinds)
    row["behaviour failure"] += bool(kinds["behaviour"])
    row["interface failure"] += bool(kinds["interface"])
    if r["grade"] == "PASS":
        for name, value in report["tests"].items():
            if value != "ok":
                failing_tests_on_passes[(r["prompt"], "interface" if INTERFACE.search(value) else "behaviour",
                                         value[:110])] += 1
columns = ["n", "any failure", "behaviour failure", "interface failure", "no runnable tests", "no tests written"]
print(f"{'prompt':6} {'grade':5} " + " ".join(f"{c:>18}" for c in columns))
for (prompt, grade), row in sorted(table.items()):
    print(f"{prompt:6} {grade:5} " + " ".join(f"{row[c]:>18}" for c in columns))
print("\nFailures on graded-PASS deliverables (prompt, kind, message): count")
for key, count in failing_tests_on_passes.most_common(30):
    print(" ", count, key)
