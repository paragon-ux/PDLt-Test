import json
from itertools import combinations

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

def optimal_pack(items, capacity):
    # simple branch-and-bound search
    items = sorted(items, reverse=True)  # place larger items first for pruning
    best = None
    def search(bins, idx):
        nonlocal best
        if best is not None and len(bins) >= len(best):
            return
        if idx == len(items):
            best = [b[:] for b in bins]
            return
        item = items[idx]
        # try to fit into existing bins
        for i, b in enumerate(bins):
            if sum(b) + item <= capacity:
                b.append(item)
                search(bins, idx+1)
                b.pop()
        # try new bin
        bins.append([item])
        search(bins, idx+1)
        bins.pop()
    search([], 0)
    return best

def self_test(first_bins, opt_bins, items, capacity):
    def check(bins):
        flat = [i for b in bins for i in b]
        return sorted(flat) == sorted(items) and all(sum(b) <= capacity for b in bins)
    return check(first_bins) and check(opt_bins)

items = [5,5,5,3,3,3,7,7]
capacity = 10
ff = first_fit(items, capacity)
opt = optimal_pack(items, capacity)
gap = len(ff) - len(opt)
assert self_test(ff, opt, items, capacity)
result = {
    "first_fit_packing": ff,
    "optimal_packing": opt,
    "gap": gap,
    "explanation": (
        "First Fit packs items in arrival order, causing fragmentation. "
        "The early 5s occupy bins leaving only 5 capacity, so later 3s cannot join them, and the 7s each need separate bins. "
        "Reordering allows pairing 7 with 3, reducing total bins."
    )
}
print("WITNESS: " + json.dumps({"polarity": "positive", "data": result}))

[host] Witness values are written into the program, not computed; unverified.

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
          7,
          3
        ],
        [
          7,
          3
        ],
        [
          5,
          5
        ],
        [
          5,
          3
        ]
      ],
      "gap": 1,
      "explanation": "First Fit packs items in arrival order, causing fragmentation. The early 5s occupy bins leaving only 5 capacity, so later 3s cannot join them, and the 7s each need separate bins. Reordering allows pairing 7 with 3, reducing total bins."
    },
    "provisional": true
  }
}
```
