import json

def solve_latin_square():
    n = 7
    # cyclic Latin square solution
    square = [[(i + j) % n + 1 for j in range(n)] for i in range(n)]
    return square

square = solve_latin_square()
# Verify rows and columns are permutations of 1..7
assert all(sorted(row) == list(range(1,8)) for row in square)
assert all(sorted([square[i][j] for i in range(7)]) == list(range(1,8)) for j in range(7))

witness = {
    "polarity": "positive",
    "data": {
        "latin_square": square
    }
}
print("WITNESS: " + json.dumps(witness))

```json
{
  "files": [],
  "reconciliation": [],
  "open_defects": [],
  "witness": {
    "polarity": "positive",
    "data": {
      "latin_square": [
        [
          1,
          2,
          3,
          4,
          5,
          6,
          7
        ],
        [
          2,
          3,
          4,
          5,
          6,
          7,
          1
        ],
        [
          3,
          4,
          5,
          6,
          7,
          1,
          2
        ],
        [
          4,
          5,
          6,
          7,
          1,
          2,
          3
        ],
        [
          5,
          6,
          7,
          1,
          2,
          3,
          4
        ],
        [
          6,
          7,
          1,
          2,
          3,
          4,
          5
        ],
        [
          7,
          1,
          2,
          3,
          4,
          5,
          6
        ]
      ]
    },
    "provisional": false
  }
}
```
