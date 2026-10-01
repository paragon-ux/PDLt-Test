```python
import json as _json

L = [71, 97, 54, 56, 44, 158, 45, 58, 82, 135, 113, 117, 86, 40, 12, 185, 63, 50, 111, 72, 90, 109, 61, 13, 92, 60, 91, 35, 114, 94, 105, 26, 15, 51, 102, 118, 76, 32, 108, 23, 22, 134, 83, 43, 64]

def find_partition(L):
    L_set = set(L)
    triples = []
    # generate all possible triples (a,b,c) such that a+b=c
    for c in L:
        for a in L:
            if a == c:
                continue
            b = c - a
            if b <= 0:
                continue
            if b == a or b == c:
                continue
            if b in L_set and b != a and b != c:
                if a <= b:
                    triples.append((a, b, c))
    triples_by_elem = {}
    for t in triples:
        for x in t:
            triples_by_elem.setdefault(x, []).append(t)
    used = set()
    solution = []
    def backtrack():
        if len(solution) == len(L) // 3:
            return True
        remaining = [x for x in L if x not in used]
        best_elem = None
        best_choices = None
        for x in remaining:
            choices = [t for t in triples_by_elem.get(x, []) if all(e not in used for e in t)]
            if not choices:
                return False
            if best_choices is None or len(choices) < len(best_choices):
                best_elem = x
                best_choices = choices
                if len(best_choices) == 1:
                    break
        for t in best_choices:
            solution.append(t)
            for e in t:
                used.add(e)
            if backtrack():
                return True
            solution.pop()
            for e in t:
                used.remove(e)
        return False
    if backtrack():
        return [list(t) for t in solution]
    return None

def main():
    solution = find_partition(L)
    if solution is not None:
        witness = {
            'polarity': 'positive',
            'evidence': {'path': 'execution://witness'},
            'data': {'triples': solution}
        }
    else:
        witness = {
            'polarity': 'negative',
            'evidence': {'path': 'execution://witness'},
            'basis': 'search',
            'search_exhausted': True,
            'nodes_explored': 0,
            'method': 'backtrack'
        }
    print('WITNESS: ' + _json.dumps(witness))

if __name__ == '__main__':
    main()
```

```json
{
  "files": [
    {
      "filename": "solution.py",
      "satisfies": [
        "R1"
      ],
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": null
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
        "observed": null
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
      "triples": [
        [
          26,
          71,
          97
        ],
        [
          50,
          61,
          111
        ],
        [
          43,
          92,
          135
        ],
        [
          12,
          44,
          56
        ],
        [
          32,
          58,
          90
        ],
        [
          15,
          102,
          117
        ],
        [
          45,
          63,
          108
        ],
        [
          22,
          91,
          113
        ],
        [
          72,
          86,
          158
        ],
        [
          23,
          82,
          105
        ],
        [
          76,
          109,
          185
        ],
        [
          13,
          51,
          64
        ],
        [
          54,
          60,
          114
        ],
        [
          40,
          94,
          134
        ],
        [
          35,
          83,
          118
        ]
      ]
    },
    "provisional": false
  }
}
```
