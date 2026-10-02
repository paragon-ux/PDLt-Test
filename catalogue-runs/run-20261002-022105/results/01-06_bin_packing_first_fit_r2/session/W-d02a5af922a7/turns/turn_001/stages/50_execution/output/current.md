import json

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

def optimal_packing(items, C):
    # Brute‑force search for minimal number of bins
    best = None
    n = len(items)
    # sort descending to improve pruning
    items_sorted = sorted(items, reverse=True)
    def backtrack(idx, bins):
        nonlocal best
        # prune if already worse than best found
        if best is not None and len(bins) >= len(best):
            return
        if idx == n:
            best = [list(b) for b in bins]
            return
        item = items_sorted[idx]
        # try existing bins
        for i in range(len(bins)):
            if sum(bins[i]) + item <= C:
                bins[i].append(item)
                backtrack(idx + 1, bins)
                bins[i].pop()
        # try new bin
        bins.append([item])
        backtrack(idx + 1, bins)
        bins.pop()
    backtrack(0, [])
    return best

def verify(packing, items, C):
    flat = [i for b in packing for i in b]
    return sorted(flat) == sorted(items) and all(sum(b) <= C for b in packing)

def main():
    C = 10
    items = [5, 5, 5, 3, 3, 3, 7, 7]
    ff = first_fit(items, C)
    opt = optimal_packing(items, C)
    gap = len(ff) - len(opt)
    explanation = "First Fit respects the arrival order, leading to sub‑optimal utilization; a different ordering can pack items tighter."
    # self‑test
    assert verify(ff, items, C)
    assert verify(opt, items, C)
    witness = {"polarity": "positive", "data": {"first_fit": ff, "optimal": opt, "gap": gap, "explanation": explanation}}
    print("WITNESS: " + json.dumps(witness))

if __name__ == "__main__":
    main()

[host] Witness values are written into the program, not computed; unverified.

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
      "explanation": "First Fit respects the arrival order, leading to sub‑optimal utilization; a different ordering can pack items tighter."
    },
    "provisional": true
  }
}
```
