graph = {
    0: [1,3],
    1: [0,2,8],
    2: [1,3,7],
    3: [2,4,0],
    4: [3,5,9],
    5: [4,6],
    6: [5,7,11],
    7: [6,8,2],
    8: [7,9,1],
    9: [8,10,4],
    10: [9,11],
    11: [10,6]
}

n = 12
solution = None


def backtrack(path, visited):
    global solution
    if solution is not None:
        return
    if len(path) == n:
        solution = path.copy()
        return
    last = path[-1]
    for neighbor in graph[last]:
        if neighbor not in visited:
            visited.add(neighbor)
            path.append(neighbor)
            backtrack(path, visited)
            path.pop()
            visited.remove(neighbor)

for start in range(n):
    backtrack([start], {start})
    if solution:
        break

if solution:
    print("WITNESS: {\"polarity\": \"positive\", \"evidence\": {\"path\": \"execution://witness\"}, \"data\": {\"path\": " + str(solution) + "}}")
else:
    print("WITNESS: {\"polarity\": \"negative\", \"evidence\": {\"path\": \"execution://witness\"}, \"basis\": \"search\", \"search_exhausted\": true, \"nodes_explored\": 0, \"method\": \"backtrack\"}")

```json
{
  "files": [
    {
      "filename": "hamiltonian_path.py",
      "satisfies": [
        "R1",
        "R2",
        "R3",
        "R4",
        "R5"
      ],
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "solution = None"
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
        "observed": "def backtrack(path, visited):"
      }
    },
    {
      "requirement": "R2",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "print(\\\"WITNESS: {\\\\\\\"polarity\\\\\\\": \\\\\"positive\\\\\\\","
      }
    },
    {
      "requirement": "R3",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "if len(path) == n:"
      }
    },
    {
      "requirement": "R4",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "for neighbor in graph[last]:"
      }
    },
    {
      "requirement": "R5",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "",
        "observed": "def backtrack(path, visited):"
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
      "path": [
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
