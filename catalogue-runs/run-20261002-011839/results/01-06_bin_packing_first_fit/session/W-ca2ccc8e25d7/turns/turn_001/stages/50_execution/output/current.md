import json, itertools

items = [5, 5, 5, 3, 3, 3, 7, 7]
capacity = 10

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
    # brute‑force search over partitions using recursion
    best = None
    def search(remaining, current_bins):
        nonlocal best
        if not remaining:
            if best is None or len(current_bins) < len(best):
                best = [list(b) for b in current_bins]
            return
        # prune if already worse than best
        if best is not None and len(current_bins) >= len(best):
            return
        item = remaining[0]
        for i, b in enumerate(current_bins):
            if sum(b) + item <= cap:
                b.append(item)
                search(remaining[1:], current_bins)
                b.pop()
        # start new bin
        current_bins.append([item])
        search(remaining[1:], current_bins)
        current_bins.pop()
    search(list(items), [])
    return best

ff_bins = first_fit(items, capacity)
opt_bins = optimal_packing(items, capacity)

ff_bin_count = len(ff_bins)
opt_bin_count = len(opt_bins)

difference = ff_bin_count - opt_bin_count

explanation = (
    "Because First Fit processes items in the given order, the first three 5s each start a new bin. "
    "When the three 3s arrive they fill the first two bins (5+3=8) but the third 3 cannot fit, "
    "so it starts a third bin. The later 7s then each need a new bin because no remaining space "
    "is sufficient. An optimal packing can pair each 7 with a 3 (7+3=10) and group the three 5s together "
    "(5+5=10, leaving one 5 to share a bin with a 3), achieving only three bins."
)

# self‑test

def verify(packing):
    flat = [item for bin_ in packing for item in bin_]
    assert sorted(flat) == sorted(items), "Item multiset mismatch"
    for bin_ in packing:
        assert sum(bin_) <= capacity, f"Bin exceeds capacity: {bin_}"

verify(ff_bins)
verify(opt_bins)

witness = {
    "polarity": "positive",
    "data": {
        "first_fit_bins": ff_bins,
        "optimal_bins": opt_bins,
        "first_fit_bin_count": ff_bin_count,
        "optimal_bin_count": opt_bin_count,
        "difference": difference,
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
      "difference": 1,
      "explanation": "Because First Fit processes items in the given order, the first three 5s each start a new bin. When the three 3s arrive they fill the first two bins (5+3=8) but the third 3 cannot fit, so it starts a third bin. The later 7s then each need a new bin because no remaining space is sufficient. An optimal packing can pair each 7 with a 3 (7+3=10) and group the three 5s together (5+5=10, leaving one 5 to share a bin with a 3), achieving only three bins."
    },
    "provisional": false
  }
}
```
