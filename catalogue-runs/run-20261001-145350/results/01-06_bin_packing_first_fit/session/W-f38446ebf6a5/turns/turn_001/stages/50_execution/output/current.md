import json

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
    # simple brute‑force search for minimal bins (small instance)
    from itertools import permutations, product
    best = None
    # generate all possible assignments of items to bins up to len(items) bins
    for k in range(1, len(items)+1):
        # create k empty bins
        bins = [[] for _ in range(k)]
        # assign items in order to bins using backtracking
        def backtrack(idx):
            nonlocal best
            if idx == len(items):
                # all items placed, check capacities
                if all(sum(b) <= capacity for b in bins):
                    best = [list(b) for b in bins]
                    return True
                return False
            item = items[idx]
            for b in bins:
                if sum(b) + item <= capacity:
                    b.append(item)
                    if backtrack(idx+1):
                        return True
                    b.pop()
            return False
        if backtrack(0):
            break
    return best

items = [5, 5, 5, 3, 3, 3, 7, 7]
capacity = 10
ff_bins = first_fit(items, capacity)
opt_bins = optimal_pack(items, capacity)
ff_count = len(ff_bins)
opt_count = len(opt_bins)
gap = ff_count - opt_count
explanation = (
    "First Fit processes items sequentially. The early 5s fill one bin, leaving another 5 that cannot share with later 3s because the bin is already full. "
    "Later, the 7s each start new bins because earlier bins lack enough residual space. "
    "An optimal arrangement pairs each 7 with a 3, and groups the 5s together, achieving four bins instead of five."
)
# self‑tests
assert sum(sum(b) for b in ff_bins) == sum(items)
assert all(sum(b) <= capacity for b in ff_bins)
assert sum(sum(b) for b in opt_bins) == sum(items)
assert all(sum(b) <= capacity for b in opt_bins)

witness = {
    "polarity": "positive",
    "data": {
        "first_fit_bins": ff_bins,
        "optimal_bins": opt_bins,
        "first_fit_bin_count": ff_count,
        "optimal_bin_count": opt_count,
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
      "first_fit_bins": [
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
      "optimal_bins": [
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
      "first_fit_bin_count": 5,
      "optimal_bin_count": 4,
      "gap": 1,
      "explanation": "First Fit processes items sequentially. The early 5s fill one bin, leaving another 5 that cannot share with later 3s because the bin is already full. Later, the 7s each start new bins because earlier bins lack enough residual space. An optimal arrangement pairs each 7 with a 3, and groups the 5s together, achieving four bins instead of five."
    },
    "provisional": false
  }
}
```
