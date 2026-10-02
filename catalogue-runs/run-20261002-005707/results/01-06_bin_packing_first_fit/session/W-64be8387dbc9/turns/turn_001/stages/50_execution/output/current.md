import json

first_fit = [[5, 5], [5, 3], [3, 3], [7], [7]]
optimal = [[7, 3], [7, 3], [5, 5], [5, 3]]
gap = len(first_fit) - len(optimal)

items = [5, 5, 5, 3, 3, 3, 7, 7]

def test(packing):
    used = []
    for bin in packing:
        assert sum(bin) <= 10, "Bin exceeds capacity"
        used.extend(bin)
    assert sorted(used) == sorted(items), "Item mismatch"

for p in (first_fit, optimal):
    test(p)

witness = {"polarity": "positive", "data": {"first_fit": first_fit, "optimal": optimal, "gap": gap}}
print("WITNESS: " + json.dumps(witness))

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
      "gap": 1
    },
    "provisional": false
  }
}
```
