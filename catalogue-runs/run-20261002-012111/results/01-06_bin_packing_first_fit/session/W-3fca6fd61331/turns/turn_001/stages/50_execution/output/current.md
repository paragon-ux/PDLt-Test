import json

def first_fit(items, cap):
    bins = []
    for item in items:
        placed = False
        for b in bins:
            if sum(b) + item <= cap:
                b.append(item)
                placed = True
                break
        if not placed:
            bins.append([item])
    return bins

def optimal_packing(items, cap):
    # simple backtracking to find minimal number of bins
    items = list(items)
    best = None
    def backtrack(bins, remaining):
        nonlocal best
        if best is not None and len(bins) >= len(best):
            return
        if not remaining:
            best = [list(b) for b in bins]
            return
        item = remaining[0]
        # try to fit into existing bins
        for i, b in enumerate(bins):
            if sum(b) + item <= cap:
                b.append(item)
                backtrack(bins, remaining[1:])
                b.pop()
        # try new bin
        bins.append([item])
        backtrack(bins, remaining[1:])
        bins.pop()
    backtrack([], items)
    return best

def validate_packing(packing, items, cap):
    flat = [x for bin in packing for x in bin]
    assert sorted(flat) == sorted(items), "Item multiset mismatch"
    for b in packing:
        assert sum(b) <= cap, f"Bin exceeds capacity: {b}"

def main():
    items = [5,5,5,3,3,3,7,7]
    C = 10
    ff = first_fit(items, C)
    opt = optimal_packing(items, C)
    gap = len(ff) - len(opt)
    # self‑test
    validate_packing(ff, items, C)
    validate_packing(opt, items, C)
    witness = {
        "polarity": "positive",
        "data": {
            "first_fit": ff,
            "optimal": opt,
            "gap": gap,
            "explanation": "Because the large items (7) arrive after the smaller items have filled bins, First Fit cannot place a 7 with a 3, resulting in an extra bin."
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
      "first_fit": [
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
      "optimal": [
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
      "explanation": "Because the large items (7) arrive after the smaller items have filled bins, First Fit cannot place a 7 with a 3, resulting in an extra bin."
    },
    "provisional": false
  }
}
```
