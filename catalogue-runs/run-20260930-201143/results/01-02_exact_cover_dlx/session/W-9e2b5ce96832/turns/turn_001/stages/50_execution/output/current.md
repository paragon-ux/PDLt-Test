#!/usr/bin/env python3
def solve():
    U = set(range(1,10))
    sets = {
        'S1': {1,2,3},
        'S2': {4,5,6},
        'S3': {7,8,9},
        'S4': {1,4,7},
        'S5': {2,5,8},
        'S6': {3,6,9},
        'S7': {1,5,9},
        'S8': {2,6,7},
        'S9': {3,4,8},
    }
    # Algorithm X recursive search
    solutions = []
    def search(partial, remaining_sets, remaining_elements):
        if not remaining_elements:
            solutions.append(list(partial))
            return
        # choose element with fewest covering sets
        elem = min(remaining_elements, key=lambda e: sum(e in s for s in remaining_sets.values()))
        for name, s in list(remaining_sets.items()):
            if elem in s:
                new_partial = partial + [name]
                new_rem_elems = remaining_elements - s
                # remove sets that intersect with chosen set
                new_rem_sets = {n: ss for n, ss in remaining_sets.items() if ss.isdisjoint(s)}
                search(new_partial, new_rem_sets, new_rem_elems)
    search([], sets, U)
    return solutions

if __name__ == "__main__":
    sols = solve()
    for sol in sols:
        print(sol)
    import json
    witness = {"polarity":"positive","evidence":{"path":"execution://witness"},"data":{"solutions":sols}}
    print("WITNESS:", json.dumps(witness))

```json
{
  "files": [
    {
      "filename": "exact_cover.py",
      "satisfies": [
        "R1",
        "R2",
        "R3"
      ],
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "def solve():"
      }
    }
  ],
  "reconciliation": [
    {
      "requirement": "R1",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "def solve():"
      }
    },
    {
      "requirement": "R2",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "def solve():"
      }
    },
    {
      "requirement": "R3",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "def solve():"
      }
    }
  ],
  "open_defects": [],
  "witness": {
    "polarity": "positive",
    "evidence": {
      "path": "execution://witness"
    },
    "data": {
      "solutions": [
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
