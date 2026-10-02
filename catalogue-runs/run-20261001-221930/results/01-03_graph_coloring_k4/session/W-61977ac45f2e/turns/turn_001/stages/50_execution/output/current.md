import json

def main():
    # Coloring for wheel graph W_11
    # Hub node 0 uses color 4, outer cycle uses colors 1,2,3 in repeating pattern
    coloring = {
        0: 4,
        1: 1,
        2: 2,
        3: 3,
        4: 1,
        5: 2,
        6: 3,
        7: 1,
        8: 2,
        9: 3,
        10: 1,
        11: 2,
    }
    witness = {"polarity": "positive", "data": {"coloring": coloring}}
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
      "coloring": {
        "0": 4,
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 1,
        "5": 2,
        "6": 3,
        "7": 1,
        "8": 2,
        "9": 3,
        "10": 1,
        "11": 2
      }
    },
    "provisional": false
  }
}
```
