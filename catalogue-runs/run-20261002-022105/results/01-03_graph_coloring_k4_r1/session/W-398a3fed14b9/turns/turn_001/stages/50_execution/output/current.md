import json

def main():
    coloring = {
        0: 1,
        1: 2,
        2: 3,
        3: 4,
        4: 2,
        5: 3,
        6: 4,
        7: 2,
        8: 3,
        9: 4,
        10: 2,
        11: 3
    }
    proof = (
        "The peripheral cycle 1-2-...-11-1 has odd length (11), "
        "so it requires at least 3 colors. Adding the hub node 0, which is "
        "adjacent to every peripheral node, forces a fourth color because "
        "the three colors used on the cycle cannot all differ from the hub's "
        "color. Therefore a 3‑coloring is impossible and 4 colors are sufficient."
    )
    witness = {
        "polarity": "positive",
        "data": {
            "coloring": coloring,
            "proof": proof
        }
    }
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
      "proof": "The peripheral cycle 1-2-...-11-1 has odd length (11), so it requires at least 3 colors. Adding the hub node 0, which is adjacent to every peripheral node, forces a fourth color because the three colors used on the cycle cannot all differ from the hub's color. Therefore a 3‑coloring is impossible and 4 colors are sufficient."
    },
    "provisional": true
  }
}
```
