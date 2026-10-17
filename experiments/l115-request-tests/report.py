"""L115 feasibility, step 3: separation per test module. A failure is 'interface' when the test could not reach the
deliverable (a name, attribute, signature or import it assumed), 'behaviour' otherwise."""
import json
import re
import sys
from collections import defaultdict

results = json.load(open(sys.argv[1], encoding="utf-8"))
INTERFACE = re.compile(r"NameError|AttributeError|TypeError|ImportError|ModuleNotFoundError|not defined|"
                       r"has no attribute|positional argument|unexpected keyword")


def kinds(report):
    out = {"interface": 0, "behaviour": 0}
    for value in report.get("tests", {}).values():
        if value == "ok":
            continue
        out["interface" if INTERFACE.search(value) else "behaviour"] += 1
    return out


table = defaultdict(lambda: {"n": 0, "any": 0, "behaviour": 0, "all_interface": 0, "incomplete": 0})
for r in results:
    row = table[(r["module"], r["grade"])]
    row["n"] += 1
    report = r["report"]
    if "incomplete" in report or "module_error" in report:
        row["incomplete"] += 1
        continue
    k = kinds(report)
    total = len(report.get("tests", {}))
    row["any"] += bool(k["interface"] + k["behaviour"])
    row["behaviour"] += bool(k["behaviour"])
    row["all_interface"] += bool(total) and k["interface"] == total
print(f"{'module':14} {'grade':5} {'n':>3} {'any fail':>9} {'behaviour fail':>15} {'every test: interface':>22} {'incomplete':>11}")
for (module, grade), row in sorted(table.items()):
    print(f"{module:14} {grade:5} {row['n']:>3} {row['any']:>9} {row['behaviour']:>15} {row['all_interface']:>22} "
          f"{row['incomplete']:>11}")
# Which tests fail on graded PASS deliverables (wrong tests, or interface assumptions).
wrong = defaultdict(int)
for r in results:
    if r["grade"] == "PASS":
        for name, value in r["report"].get("tests", {}).items():
            if value != "ok":
                wrong[(r["module"], name, "interface" if INTERFACE.search(value) else "behaviour")] += 1
print("\nTests failing on graded-PASS deliverables (module, test, kind): count")
for key, count in sorted(wrong.items(), key=lambda x: -x[1])[:25]:
    print(" ", key, count)
