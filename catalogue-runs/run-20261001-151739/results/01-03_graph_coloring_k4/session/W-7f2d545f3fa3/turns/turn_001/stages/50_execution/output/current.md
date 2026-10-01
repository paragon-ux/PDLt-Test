import json

def four_coloring_wheel():
    # Define colors for nodes 0 (hub) and 1-11 (peripheral)
    coloring = {
        0: 1,
        1: 2,
        2: 3,
        3: 2,
        4: 3,
        5: 2,
        6: 3,
        7: 2,
        8: 3,
        9: 2,
        10: 3,
        11: 4  # fourth color needed to close the odd cycle
    }
    return coloring

def proof_three_color_impossible():
    proof = (
        "The peripheral nodes 1‑11 form an odd cycle of length 11. "
        "An odd cycle requires at least 3 colors because a 2‑coloring would alternate colors, "
        "forcing the first and last vertices to share a color, which contradicts adjacency. "
        "Thus the peripheral cycle needs 3 distinct colors. "
        "The hub node 0 is adjacent to every peripheral node, so its color must differ from each of the three colors used on the cycle. "
        "Consequently a fourth color is required, proving that a 3‑coloring of W_11 is impossible."
    )
    return proof

def main():
    coloring = four_coloring_wheel()
    proof = proof_three_color_impossible()
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
        "3": 2,
        "4": 3,
        "5": 2,
        "6": 3,
        "7": 2,
        "8": 3,
        "9": 2,
        "10": 3,
        "11": 4
      },
      "proof": "The peripheral nodes 1‑11 form an odd cycle of length 11. An odd cycle requires at least 3 colors because a 2‑coloring would alternate colors, forcing the first and last vertices to share a color, which contradicts adjacency. Thus the peripheral cycle needs 3 distinct colors. The hub node 0 is adjacent to every peripheral node, so its color must differ from each of the three colors used on the cycle. Consequently a fourth color is required, proving that a 3‑coloring of W_11 is impossible."
    },
    "provisional": false
  }
}
```
