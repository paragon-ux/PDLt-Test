import json

def find_coloring():
    # Colors 1..4
    colors = {i: None for i in range(12)}  # nodes 0..11
    # assign hub node 0 color 4
    colors[0] = 4
    # assign peripheral cycle alternating 1,2,3
    # cycle length 11 (odd), use pattern 1,2,3,1,2,3,...
    pattern = [1,2,3]
    for idx, node in enumerate(range(1,12)):
        colors[node] = pattern[idx % 3]
    # check conflicts with hub (node 0) - hub color 4 distinct, ok
    # check adjacent peripheral nodes
    for i in range(1,12):
        j = i+1 if i<11 else 1
        if colors[i]==colors[j]:
            # conflict, adjust one node to color 4
            colors[j]=4
    return colors

col = find_coloring()
# verify
valid = True
edges = [(0,i) for i in range(1,12)] + [(i,i+1) for i in range(1,11)] + [(11,1)]
for u,v in edges:
    if col[u]==col[v]:
        valid=False
        break
witness = {"polarity":"positive","evidence":{"path":"execution://witness"},"data":{"coloring":col,"valid":valid}}
print("WITNESS: "+json.dumps(witness))

```json
{
  "files": [
    {
      "filename": "wheel_coloring.py",
      "satisfies": [
        "R1",
        "R2"
      ],
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "def find_coloring():\\n    # Colors 1..4\\n    colors = {i: None for i in range(12)}  # nodes 0..11\\n    # assign hub node 0 color 4\\n    colors[0] = 4\\n    # assign peripheral cycle alternating 1,2,3\\n    # cycle length 11 (odd), use pattern 1,2,3,1,2,3,...\\n    pattern = [1,2,3]\\n    for idx, node in enumerate(range(1,12)):\\n        colors[node] = pattern[idx % 3]\\n    # check conflicts with hub (node 0) - hub color 4 distinct, ok\\n    # check adjacent peripheral nodes\\n    for i in range(1,12):\\n        j = i+1 if i<11 else 1\\n        if colors[i]==colors[j]:\\n            # conflict, adjust one node to color 4\\n            colors[j]=4\\n    return colors"
      }
    }
  ],
  "reconciliation": [
    {
      "requirement": "R1",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "def find_coloring(): ... return colors"
      }
    },
    {
      "requirement": "R2",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "# assign peripheral cycle alternating 1,2,3 ... hub color 4 distinct, ok"
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
      },
      "valid": true
    },
    "provisional": false
  }
}
```
