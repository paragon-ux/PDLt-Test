import json

def main():
    # Simple Hamiltonian path using the sequential edges 0-1-2-...-11
    path = list(range(12))
    witness = {
        "polarity": "positive",
        "data": {"hamiltonian_path": path}
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
      "hamiltonian_path": [
        0,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11
      ]
    },
    "provisional": false
  }
}
```
