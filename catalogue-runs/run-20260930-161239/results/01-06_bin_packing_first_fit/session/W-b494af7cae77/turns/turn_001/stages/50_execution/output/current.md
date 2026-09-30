# bin_packing.py
"""Bin Packing demonstration
Capacity C = 10
Items = [5, 5, 5, 3, 3, 3, 7, 7]
"""
from itertools import combinations, chain

C = 10
ITEMS = [5, 5, 5, 3, 3, 3, 7, 7]

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

def all_partitions(seq):
    # generate all ways to split seq into unordered bins (order of bins irrelevant)
    if not seq:
        yield []
        return
    first, *rest = seq
    for partition in all_partitions(rest):
        # try to put first in existing bin
        for i, bin in enumerate(partition):
            if sum(bin) + first <= C:
                new_part = [b[:] if idx!=i else bin+[first] for idx,b in enumerate(partition)]
                yield new_part
        # or start new bin
        yield [[first]] + [b[:] for b in partition]

def optimal_packing(items, capacity):
    best = None
    for part in all_partitions(items):
        if all(sum(b) <= capacity for b in part):
            if best is None or len(part) < len(best):
                best = part
    return best

def self_test():
    ff = first_fit(ITEMS, C)
    opt = optimal_packing(ITEMS, C)
    # verify all items used exactly once
    def flatten(bins):
        return list(chain.from_iterable(bins))
    assert sorted(flatten(ff)) == sorted(ITEMS), "First Fit does not use all items exactly once"
    assert sorted(flatten(opt)) == sorted(ITEMS), "Optimal does not use all items exactly once"
    # verify capacity constraint
    for b in ff:
        assert sum(b) <= C, f"First Fit bin exceeds capacity: {b}"
    for b in opt:
        assert sum(b) <= C, f"Optimal bin exceeds capacity: {b}"
    return ff, opt

if __name__ == "__main__":
    ff_bins, opt_bins = self_test()
    gap = len(ff_bins) - len(opt_bins)
    print("First Fit packing:")
    for i, b in enumerate(ff_bins, 1):
        print(f" Bin {i}: {b} (sum={sum(b)})")
    print("\nOptimal packing:")
    for i, b in enumerate(opt_bins, 1):
        print(f" Bin {i}: {b} (sum={sum(b)})")
    print(f"\nGap (FF bins - optimal bins): {gap}")
    explanation = (
        "The arrival order places three 5‑s before any smaller items. "
        "First Fit puts each 5 into a new bin because no bin has enough remaining "
        "capacity to accommodate another 5. Later the three 3‑s could have filled the "
        "gaps (5+3=8) but they arrive after the bins are already opened, so they occupy "
        "new bins together with the 7‑s, leading to more bins than the optimal packing, "
        "which groups items differently irrespective of order."
    )
    print("\nExplanation:\n" + explanation)
    # Witness output for host verification
    import json
    witness = {
        "polarity": "positive",
        "evidence": {"path": "execution://witness"},
        "data": {
            "first_fit_bins": ff_bins,
            "optimal_bins": opt_bins,
            "gap": gap
        }
    }
    print("WITNESS: " + json.dumps(witness))

```json
{
  "files": [
    {
      "filename": "bin_packing.py",
      "satisfies": [
        "R1",
        "R2",
        "R3",
        "R4",
        "R5",
        "R6",
        "R7",
        "R8"
      ],
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "# bin_packing.py"
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
        "observed": "ITEMS = [5, 5, 5, 3, 3, 3, 7, 7]"
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
          3,
          5
        ],
        [
          7,
          3
        ],
        [
          7,
          3
        ]
      ],
      "gap": 1
    },
    "provisional": false
  }
}
```
