import json
from itertools import combinations

def exact_covers():
    # Universe
    U = set(range(1, 10))
    # Sets
    sets = {
        'S1': {1, 2, 3},
        'S2': {4, 5, 6},
        'S3': {7, 8, 9},
        'S4': {1, 4, 7},
        'S5': {2, 5, 8},
        'S6': {3, 6, 9},
        'S7': {1, 5, 9},
        'S8': {2, 6, 7},
        'S9': {3, 4, 8},
    }
    names = list(sets.keys())
    solutions = []
    # Exact cover must have exactly 3 sets because each set has size 3 and |U|=9
    for combo in combinations(names, 3):
        union = set()
        disjoint = True
        for name in combo:
            s = sets[name]
            if union & s:
                disjoint = False
                break
            union |= s
        if disjoint and union == U:
            solutions.append(list(combo))
    return solutions

def verify(solutions):
    U = set(range(1, 10))
    sets = {
        'S1': {1, 2, 3},
        'S2': {4, 5, 6},
        'S3': {7, 8, 9},
        'S4': {1, 4, 7},
        'S5': {2, 5, 8},
        'S6': {3, 6, 9},
        'S7': {1, 5, 9},
        'S8': {2, 6, 7},
        'S9': {3, 4, 8},
    }
    for sol in solutions:
        covered = set()
        for name in sol:
            covered |= sets[name]
        assert covered == U, f"Solution {sol} does not cover U"
        # ensure each element appears exactly once
        counts = {i:0 for i in U}
        for name in sol:
            for i in sets[name]:
                counts[i] += 1
        assert all(c == 1 for c in counts.values()), f"Solution {sol} has duplicate coverage"

if __name__ == "__main__":
    sols = exact_covers()
    verify(sols)
    witness = {
        "polarity": "positive",
        "data": {
            "exact_covers": sols
        }
    }
    print("WITNESS: " + json.dumps(witness))

```json
{
  "files": [],
  "reconciliation": [],
  "open_defects": [],
  "witness": {
    "polarity": "positive",
    "data": {
      "exact_covers": [
        [
          "S1",
          "S2",
          "S3"
        ],
        [
          "S4",
          "S5",
          "S6"
        ],
        [
          "S7",
          "S8",
          "S9"
        ]
      ]
    },
    "provisional": false
  }
}
```
