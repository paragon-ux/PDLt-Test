#!/usr/bin/env python3
import json

def main():
    # Assign colors to nodes of wheel graph W_11
    # Colors are integers 1..4
    colors = {
        0: 4,  # central hub gets the fourth color
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
    witness = {
        "polarity": "positive",
        "data": {
            "description": "Valid 4‑coloring for wheel graph W_11",
            "colors": colors
        }
    }
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
      "description": "Valid 4‑coloring for wheel graph W_11",
      "colors": {
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
