import json, sys

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
    # brute‑force search using recursion
    best = None
    def backtrack(remaining, current_bins):
        nonlocal best
        if best is not None and len(current_bins) >= len(best):
            return
        if not remaining:
            best = [list(b) for b in current_bins]
            return
        item = remaining[0]
        for i, b in enumerate(current_bins):
            if sum(b) + item <= cap:
                b.append(item)
                backtrack(remaining[1:], current_bins)
                b.pop()
        # try new bin
        current_bins.append([item])
        backtrack(remaining[1:], current_bins)
        current_bins.pop()
    backtrack(items, [])
    return best

ff = first_fit(items, capacity)
opt = optimal_packing(items, capacity)
gap = len(ff) - len(opt)

print("First Fit packing:", ff)
print("Optimal packing:", opt)
print("Gap (bins):", gap)
print("\nExplanation: First Fit places items greedily in the order given, which prevents later items from being paired optimally. In this instance the two 7‑s are each placed alone because earlier 5‑s fill bins, whereas the optimal packing can combine a 7 with a 3.")

# self‑test
def validate(packing):
    flat = [i for bin in packing for i in bin]
    assert sorted(flat) == sorted(items), "Item mismatch"
    for b in packing:
        assert sum(b) <= capacity, "Capacity exceeded"
validate(ff)
validate(opt)

witness = {
    "polarity": "positive",
    "evidence": {"path": "execution://witness"},
    "data": {
        "first_fit_bins": len(ff),
        "optimal_bins": len(opt),
        "gap": gap
    }
}
print("WITNESS:", json.dumps(witness))

```json
{
  "files": [
    {
      "filename": "packing.py",
      "satisfies": [
        "R1",
        "R2",
        "R3",
        "R4",
        "R5",
        "R6"
      ],
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "First Fit packing:"
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
        "observed": "First Fit packing:"
      }
    },
    {
      "requirement": "R2",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "Optimal packing:"
      }
    },
    {
      "requirement": "R3",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "Gap (bins):"
      }
    },
    {
      "requirement": "R4",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "Explanation:"
      }
    },
    {
      "requirement": "R5",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "self‑test"
      }
    },
    {
      "requirement": "R6",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "def first_fit"
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
      "first_fit_bins": 5,
      "optimal_bins": 4,
      "gap": 1
    },
    "provisional": false
  }
}
```
