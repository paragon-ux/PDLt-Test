# coloring.py

def color_wheel():
    colors = [1, 2, 3, 4]
    # Assign colors to the 11‑node odd cycle using three colors cyclically
    assignment = {}
    cycle_colors = [1, 2, 3]
    for i in range(1, 12):
        assignment[i] = cycle_colors[(i - 1) % 3]
    # Hub node 0 is adjacent to every cycle node, so it must use the fourth color
    assignment[0] = 4
    return assignment

if __name__ == "__main__":
    assign = color_wheel()
    import json
    witness = {
        "polarity": "positive",
        "evidence": {"path": "execution://witness"},
        "data": {
            "coloring": assign,
            "proof": "The 11‑node cycle is odd and requires three distinct colors; the hub is adjacent to all cycle nodes, so it cannot reuse any of those three colors and therefore needs a fourth color."
        }
    }
    print("WITNESS:", json.dumps(witness))

```json
{
  "files": [
    {
      "filename": "coloring.py",
      "satisfies": [
        "R1",
        "R2",
        "R3",
        "R4",
        "R5"
      ],
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "def color_wheel():\\n    colors = [1, 2, 3, 4]"
      }
    }
  ],
  "reconciliation": [
    {
      "requirement": "R1",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "# coloring.py"
      }
    },
    {
      "requirement": "R2",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "colors = [1, 2, 3, 4]"
      }
    },
    {
      "requirement": "R3",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "assignment[i] = cycle_colors[(i - 1) % 3]"
      }
    },
    {
      "requirement": "R4",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "assignment[0] = 4"
      }
    },
    {
      "requirement": "R5",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "proof\": \\\"The 11‑node cycle is odd and requires three distinct colors; the hub is adjacent to all cycle nodes, so it cannot reuse any of those three colors and therefore needs a fourth color.\\\""
      }
    }
  ],
  "open_defects": [],
  "witness": {
    "polarity": "positive",
    "evidence": {
      "path": "execution://witness"
    },
    "data": {
      "coloring": {
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
        "11": 2,
        "0": 4
      },
      "proof": "The 11‑node cycle is odd and requires three distinct colors; the hub is adjacent to all cycle nodes, so it cannot reuse any of those three colors and therefore needs a fourth color."
    },
    "provisional": false
  }
}
```
