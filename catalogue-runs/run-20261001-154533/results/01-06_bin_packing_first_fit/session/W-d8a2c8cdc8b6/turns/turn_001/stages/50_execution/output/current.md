import json
from itertools import product

def first_fit(items, capacity):
    bins = []
    for item in items:
        placed = False
        for b in bins:
            if sum(b) + item <= capacity:
                b.append(item)
                placed = True
                break
        if not placed:
            bins.append([item])
    return bins

def optimal_packing(items, capacity):
    # simple backtracking to find minimal number of bins
    best = None
    n = len(items)
    items = list(items)
    def backtrack(idx, bins):
        nonlocal best
        if best is not None and len(bins) >= len(best):
            return
        if idx == n:
            best = [list(b) for b in bins]
            return
        item = items[idx]
        for i, b in enumerate(bins):
            if sum(b) + item <= capacity:
                b.append(item)
                backtrack(idx+1, bins)
                b.pop()
        # try new bin
        bins.append([item])
        backtrack(idx+1, bins)
        bins.pop()
    backtrack(0, [])
    return best

def verify_packing(packing, items, capacity):
    flat = [i for b in packing for i in b]
    assert sorted(flat) == sorted(items), "Items mismatch"
    for b in packing:
        assert sum(b) <= capacity, "Bin exceeds capacity"

def main():
    items = [5,5,5,3,3,3,7,7]
    C = 10
    ff = first_fit(items, C)
    opt = optimal_packing(items, C)
    gap = len(ff) - len(opt)
    explanation = (
        "First Fit processes items in the given order, causing early placement of 5s and 3s "
        "that leaves insufficient space for later 7s, resulting in more bins than the optimal "
        "arrangement which pairs each 7 with a 3 and groups the remaining 5s efficiently."
    )
    # self‑test
    verify_packing(ff, items, C)
    verify_packing(opt, items, C)
    # produce witness
    witness = {
        "polarity": "positive",
        "data": {
            "first_fit_packing": ff,
            "optimal_packing": opt,
            "gap": gap,
            "explanation": explanation
        }
    }
    print("WITNESS: " + json.dumps(witness))

if __name__ == "__main__":
    main()

```json
{
  "files": [],
  "reconciliation": [],
  "open_defects": [],
  "witness": {
    "polarity": "positive",
    "data": {
      "first_fit_packing": [
        [
          5,
          5
        ],
        [
          5,
          3
        ],
        [
          3,
          3
        ],
        [
          7
        ],
        [
          7
        ]
      ],
      "optimal_packing": [
        [
          5,
          5
        ],
        [
          5,
          3
        ],
        [
          3,
          7
        ],
        [
          3,
          7
        ]
      ],
      "gap": 1,
      "explanation": "First Fit processes items in the given order, causing early placement of 5s and 3s that leaves insufficient space for later 7s, resulting in more bins than the optimal arrangement which pairs each 7 with a 3 and groups the remaining 5s efficiently."
    },
    "provisional": false
  }
}
```
