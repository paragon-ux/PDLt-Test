import json

# Color assignment for wheel graph W_11
# Hub node 0 gets color 1. Outer nodes 1-11 are colored cyclically with 2,3,4.
color_assignment = {
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
    11: 3,
}

proof = (
    "The outer cycle of W_11 has 11 vertices, which is odd. "
    "An odd cycle cannot be properly colored with only 2 colors, "
    "so at least 3 colors are needed for the outer vertices. "
    "The hub vertex 0 is adjacent to every outer vertex, therefore its color must differ from each outer vertex's color. "
    "If only 3 colors were available, the hub would be forced to use one of the three colors already used on the outer cycle, causing a conflict with at least one adjacent outer vertex. "
    "Hence a fourth color is required, and the assignment above uses exactly four colors, satisfying all adjacency constraints."
)

witness = {
    "polarity": "positive",
    "data": {
        "color_assignment": color_assignment,
        "proof": proof
    }
}

print("WITNESS: " + json.dumps(witness))

[host] Witness values are written into the program, not computed; unverified.

```json
{
  "files": [],
  "reconciliation": [],
  "open_defects": [],
  "witness": {
    "polarity": "positive",
    "data": {
      "color_assignment": {
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
      "proof": "The outer cycle of W_11 has 11 vertices, which is odd. An odd cycle cannot be properly colored with only 2 colors, so at least 3 colors are needed for the outer vertices. The hub vertex 0 is adjacent to every outer vertex, therefore its color must differ from each outer vertex's color. If only 3 colors were available, the hub would be forced to use one of the three colors already used on the outer cycle, causing a conflict with at least one adjacent outer vertex. Hence a fourth color is required, and the assignment above uses exactly four colors, satisfying all adjacency constraints."
    },
    "provisional": true
  }
}
```
