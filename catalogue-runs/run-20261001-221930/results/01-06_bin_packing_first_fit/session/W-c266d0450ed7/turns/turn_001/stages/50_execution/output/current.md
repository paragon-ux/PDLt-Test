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

def optimal_pack(items, capacity):
    # simple recursive search for minimal number of bins
    best = None
    n = len(items)
    def search(idx, bins):
        nonlocal best
        if best is not None and len(bins) >= len(best):
            return
        if idx == n:
            best = [list(b) for b in bins]
            return
        item = items[idx]
        # try to fit in existing bins
        for i, b in enumerate(bins):
            if sum(b) + item <= capacity:
                b.append(item)
                search(idx+1, bins)
                b.pop()
        # try new bin
        bins.append([item])
        search(idx+1, bins)
        bins.pop()
    search(0, [])
    return best

def self_test(ff, opt, items, capacity):
    def check(packing):
        flat = [i for bin_ in packing for i in bin_]
        assert sorted(flat) == sorted(items), "Item usage mismatch"
        for bin_ in packing:
            assert sum(bin_) <= capacity, "Capacity exceeded"
    check(ff)
    check(opt)

C = 10
items = [5, 5, 5, 3, 3, 3, 7, 7]
ff_packing = first_fit(items, C)
opt_packing = optimal_pack(items, C)
self_test(ff_packing, opt_packing, items, C)

gap = len(ff_packing) - len(opt_packing)
explanation = (
    "First Fit processes items in the given arrival order. \n"
    "Because it cannot reorganize earlier decisions, the three 5s each start new bins, \n"
    "leaving little room for the following 3s, which then each need new bins as well. \n"
    "The two 7s finally occupy bins that could have been combined with a 3 if items were reordered. \n"
    "An optimal packing can arrange items as [5,5], [5,3,3], [7,3], [7] using only 4 bins, \n"
    "where First Fit uses 5 bins."
)

witness = {
    "polarity": "positive",
    "data": {
        "first_fit_packing": ff_packing,
        "optimal_packing": opt_packing,
        "gap": gap,
        "explanation": explanation
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
      "explanation": "First Fit processes items in the given arrival order. \nBecause it cannot reorganize earlier decisions, the three 5s each start new bins, \nleaving little room for the following 3s, which then each need new bins as well. \nThe two 7s finally occupy bins that could have been combined with a 3 if items were reordered. \nAn optimal packing can arrange items as [5,5], [5,3,3], [7,3], [7] using only 4 bins, \nwhere First Fit uses 5 bins."
    },
    "provisional": false
  }
}
```
