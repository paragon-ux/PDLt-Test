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
    # Brute‑force search for minimal number of bins (small instance)
    best = None
    n = len(items)
    items_sorted = sorted(items, reverse=True)
    def backtrack(idx, bins):
        nonlocal best
        if best is not None and len(bins) >= len(best):
            return
        if idx == n:
            best = [list(b) for b in bins]
            return
        item = items_sorted[idx]
        # try to put in existing bins
        for b in bins:
            if sum(b) + item <= capacity:
                b.append(item)
                backtrack(idx + 1, bins)
                b.pop()
        # start a new bin
        bins.append([item])
        backtrack(idx + 1, bins)
        bins.pop()
    backtrack(0, [])
    return best

def self_test(ff_bins, opt_bins, items, capacity):
    def check(bins):
        flat = [i for bin in bins for i in bin]
        return sorted(flat) == sorted(items) and all(sum(bin) <= capacity for bin in bins)
    return check(ff_bins) and check(opt_bins)

def main():
    capacity = 10
    items = [5, 5, 5, 3, 3, 3, 7, 7]
    ff = first_fit(items, capacity)
    opt = optimal_pack(items, capacity)
    gap = len(ff) - len(opt)
    test_ok = self_test(ff, opt, items, capacity)
    result = {
        "first_fit": ff,
        "optimal": opt,
        "gap": gap,
        "explanation": "First Fit places items in arrival order; early 5s and 3s fill bins that later 7s could have paired with, leading to an extra bin.",
        "self_test_passed": test_ok
    }
    witness = {"polarity": "positive", "data": result}
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
      "explanation": "First Fit places items in arrival order; early 5s and 3s fill bins that later 7s could have paired with, leading to an extra bin.",
      "self_test_passed": true
    },
    "provisional": false
  }
}
```
