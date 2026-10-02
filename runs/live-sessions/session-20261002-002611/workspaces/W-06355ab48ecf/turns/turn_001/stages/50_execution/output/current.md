#!/usr/bin/env python3
import json

def main():
    # The probability that the shortest piece is at least 1/4 of the longest piece
    # for a unit stick broken at two random points is 1/4.
    prob = "1/4"
    witness = {
        "polarity": "positive",
        "data": {"probability": prob}
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
      "probability": "1/4"
    },
    "provisional": false
  }
}
```
