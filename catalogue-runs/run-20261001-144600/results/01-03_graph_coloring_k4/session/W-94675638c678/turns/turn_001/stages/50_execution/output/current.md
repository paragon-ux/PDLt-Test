import json
coloring = {0: 1, 1: 2, 2: 3, 3: 4, 4: 2, 5: 3, 6: 4, 7: 2, 8: 3, 9: 4, 10: 2, 11: 3}
proof = "The peripheral cycle has 11 nodes, requiring at least 3 colors. With hub node adjacent to all peripherals, a fourth color is needed."
witness = {"polarity": "positive", "data": {"coloring": coloring, "proof": proof}}
print("WITNESS: " + json.dumps(witness))

```json
{
  "files": [],
  "reconciliation": [],
  "open_defects": [],
  "witness": {
    "polarity": "positive",
    "data": {
      "coloring": {
        "0": 1,
        "1": 2,
        "2": 3,
        "3": 4,
        "4": 2,
        "5": 3,
        "6": 4,
        "7": 2,
        "8": 3,
        "9": 4,
        "10": 2,
        "11": 3
      },
      "proof": "The peripheral cycle has 11 nodes, requiring at least 3 colors. With hub node adjacent to all peripherals, a fourth color is needed."
    },
    "provisional": false
  }
}
```
