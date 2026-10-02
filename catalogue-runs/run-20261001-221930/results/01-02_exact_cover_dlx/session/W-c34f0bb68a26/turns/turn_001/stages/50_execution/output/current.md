import json

# Define universe and sets
U = set(range(1, 10))
sets = {
    'S1': {1, 2, 3},
    'S2': {4, 5, 6},
    'S3': {7, 8, 9},
    'S4': {1, 4, 7},
    'S5': {2, 5, 8},
    'S6': {3, 6, 9},
    'S7': {1, 5, 9},
    'S8': {2, 6, 7},
    'S9': {3, 4, 8},
}

# Helper: check if a collection of set names forms an exact cover
def is_exact_cover(selected_names):
    covered = set()
    for name in selected_names:
        s = sets[name]
        # overlap detection
        if covered & s:
            return False
        covered |= s
    return covered == U

# Recursive search for exact covers (Algorithm X style)
solutions = []

def search(partial, remaining_sets, remaining_elements):
    if not remaining_elements:
        # all elements covered
        solutions.append(list(partial))
        return
    # Choose an element with fewest covering sets (heuristic)
    elem = min(remaining_elements, key=lambda e: sum(e in sets[name] for name in remaining_sets))
    # Iterate over sets that cover this element
    for name in list(remaining_sets):
        if elem in sets[name]:
            new_partial = partial + [name]
            new_remaining_elements = remaining_elements - sets[name]
            # Remove conflicting sets
            new_remaining_sets = {n for n in remaining_sets if sets[n].isdisjoint(sets[name])}
            search(new_partial, new_remaining_sets, new_remaining_elements)

search([], set(sets.keys()), U)

# Verify each solution
for sol in solutions:
    assert is_exact_cover(sol), f"Invalid solution: {sol}"

# Prepare witness output
witness = {
    "polarity": "positive",
    "data": {
        "solutions": solutions
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
      "solutions": [
        [
          "S7",
          "S8",
          "S9"
        ],
        [
          "S4",
          "S5",
          "S6"
        ],
        [
          "S1",
          "S2",
          "S3"
        ]
      ]
    },
    "provisional": false
  }
}
```
