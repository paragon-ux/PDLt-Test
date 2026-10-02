import json
from itertools import product

items = [5,5,5,3,3,3,7,7]
C = 10

def first_fit(items, C):
    bins = []
    for item in items:
        placed = False
        for b in bins:
            if sum(b) + item <= C:
                b.append(item)
                placed = True
                break
        if not placed:
            bins.append([item])
    return bins

def optimal_pack(items, C):
    # simple brute-force search for minimal bins using backtracking
    best = None
    def backtrack(idx, bins):
        nonlocal best
        if best is not None and len(bins) >= len(best):
            return
        if idx == len(items):
            best = [list(b) for b in bins]
            return
        item = items[idx]
        for i, b in enumerate(bins):
            if sum(b) + item <= C:
                b.append(item)
                backtrack(idx+1, bins)
                b.pop()
        # try new bin
        bins.append([item])
        backtrack(idx+1, bins)
        bins.pop()
    backtrack(0, [])
    return best

def self_test(ff_bins, opt_bins, items, C):
    def check(bins):
        flat = [x for b in bins for x in b]
        return sorted(flat) == sorted(items) and all(sum(b) <= C for b in bins)
    return check(ff_bins) and check(opt_bins)

ff = first_fit(items, C)
opt = optimal_pack(items, C)
gap = len(ff) - len(opt)
assert self_test(ff, opt, items, C)

witness = {
    "polarity": "positive",
    "data": {
        "first_fit_packing": ff,
        "optimal_packing": opt,
        "gap": gap,
        "explanation": "The arrival order places three 5s before any 3s, causing the first two 5s to occupy bins alone (5+5 would exceed capacity). When 3s arrive they cannot fill those bins, leading to more bins than optimal."
    }
}
print('WITNESS: ' + json.dumps(witness))

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
      "explanation": "The arrival order places three 5s before any 3s, causing the first two 5s to occupy bins alone (5+5 would exceed capacity). When 3s arrive they cannot fill those bins, leading to more bins than optimal."
    },
    "provisional": true
  }
}
```
