```python
### greedy_vertex_cover.py
"""
Greedy approximation for minimum vertex cover on the specified 50‑node regular graph.
The algorithm repeatedly selects the vertex with the highest current degree,
adds it to the cover, and removes all incident edges until no edges remain.
The resulting set is labeled as a non‑optimal approximation.
"""

def build_graph(num_nodes=50):
    edges = set()
    for i in range(num_nodes):
        for offset in (1, 7, 13):
            j = (i + offset) % num_nodes
            edge = tuple(sorted((i, j)))
            edges.add(edge)
    # adjacency list
    adj = {i: set() for i in range(num_nodes)}
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    return adj

def greedy_vertex_cover(adj):
    cover = set()
    # copy adjacency
    adj = {v: set(neigh) for v, neigh in adj.items()}
    while True:
        # find any remaining edge
        remaining = [(v, len(neigh)) for v, neigh in adj.items() if neigh]
        if not remaining:
            break
        # vertex with highest degree
        v, _ = max(remaining, key=lambda x: x[1])
        cover.add(v)
        # remove v and its incident edges
        for u in list(adj[v]):
            adj[u].discard(v)
        adj[v].clear()
    return sorted(cover)

if __name__ == "__main__":
    graph = build_graph()
    approx_cover = greedy_vertex_cover(graph)
    print("Approximate vertex cover (size {}):".format(len(approx_cover)), approx_cover)
    # Witness certification
    import json
    witness = {
        "polarity": "positive",
        "evidence": {"path": "execution://witness"},
        "data": {"solution": approx_cover}
    }
    print("WITNESS: " + json.dumps(witness))
```

```json
{
  "files": [
    {
      "filename": "greedy_vertex_cover.py",
      "satisfies": [
        "R1"
      ],
      "evidence": {
        "path": "execution://body",
        "section": "### greedy_vertex_cover.py",
        "observed": "def greedy_vertex_cover(adj):
    cover = set()
    # copy adjacency
    adj = {v: set(neigh) for v, neigh in adj.items()}
    while True:
        # find any remaining edge
        remaining = [(v, len(neigh)) for v, neigh in adj.items() if neigh]
        if not remaining:
            break
        # vertex with highest degree
        v, _ = max(remaining, key=lambda x: x[1])
        cover.add(v)
        # remove v and its incident edges
        for u in list(adj[v]):
            adj[u].discard(v)
        adj[v].clear()
    return sorted(cover)"
      }
    }
  ],
  "reconciliation": [
    {
      "requirement": "R1",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "### greedy_vertex_cover.py",
        "observed": "def greedy_vertex_cover(adj):
    cover = set()
    # copy adjacency
    adj = {v: set(neigh) for v, neigh in adj.items()}
    while True:
        # find any remaining edge
        remaining = [(v, len(neigh)) for v, neigh in adj.items() if neigh]
        if not remaining:
            break
        # vertex with highest degree
        v, _ = max(remaining, key=lambda x: x[1])
        cover.add(v)
        # remove v and its incident edges
        for u in list(adj[v]):
            adj[u].discard(v)
        adj[v].clear()
    return sorted(cover)"
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
      "solution": [
        0,
        2,
        4,
        6,
        8,
        10,
        12,
        14,
        16,
        18,
        20,
        22,
        24,
        26,
        28,
        30,
        32,
        34,
        36,
        38,
        40,
        42,
        44,
        46,
        48
      ]
    }
  }
}
```
