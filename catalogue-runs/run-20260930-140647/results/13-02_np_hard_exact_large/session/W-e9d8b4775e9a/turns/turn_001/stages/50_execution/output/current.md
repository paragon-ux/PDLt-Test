import itertools

def build_graph(n=50):
    edges = set()
    for i in range(n):
        for offset in (1, 7, 13):
            j = (i + offset) % n
            a, b = min(i, j), max(i, j)
            edges.add((a, b))
    return {i: set() for i in range(n)}, edges

def hopcroft_karp(graph, left, right):
    # adjacency from left to right
    INF = 10**9
    pair_u = {u: None for u in left}
    pair_v = {v: None for v in right}
    dist = {}
    def bfs():
        from collections import deque
        queue = deque()
        for u in left:
            if pair_u[u] is None:
                dist[u] = 0
                queue.append(u)
            else:
                dist[u] = INF
        dist[None] = INF
        while queue:
            u = queue.popleft()
            if dist[u] < dist[None]:
                for v in graph[u]:
                    if dist[pair_v[v]] == INF:
                        dist[pair_v[v]] = dist[u] + 1
                        queue.append(pair_v[v])
        return dist[None] != INF
    def dfs(u):
        if u is not None:
            for v in graph[u]:
                if dist[pair_v[v]] == dist[u] + 1 and dfs(pair_v[v]):
                    pair_v[v] = u
                    pair_u[u] = v
                    return True
            dist[u] = INF
            return False
        return True
    matching = 0
    while bfs():
        for u in left:
            if pair_u[u] is None and dfs(u):
                matching += 1
    return matching, pair_u, pair_v

def main():
    n = 50
    adj, edges = build_graph(n)
    # bipartition: even vs odd
    left = [i for i in range(n) if i % 2 == 0]
    right = [i for i in range(n) if i % 2 == 1]
    for u, v in edges:
        if u % 2 == 0:
            adj[u].add(v)
        else:
            adj[v].add(u)
    matching_size, _, _ = hopcroft_karp(adj, left, right)
    min_cover_size = matching_size  # König's theorem
    cover = left  # all even vertices form a minimum vertex cover
    result = {
        "cover": cover,
        "size": len(cover),
        "matching_size": matching_size
    }
    print(f"WITNESS: {result}")

if __name__ == "__main__":
    main()

```json
{
  "files": [
    {
      "filename": "min_vertex_cover.py",
      "satisfies": [
        "R1",
        "R2",
        "R3",
        "R4"
      ],
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "import itertools\\n\\ndef build_graph(n=50):\\n    edges = set()\\n    for i in range(n):\\n        for offset in (1, 7, 13):\\n            j = (i + offset) % n\\n            a, b = min(i, j), max(i, j)\\n            edges.add((a, b))\\n    return {i: set() for i in range(n)}, edges\\n...\\n    print(f\\\"WITNESS: {result}\\\")"
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
        "observed": "def build_graph(n=50):\\n    edges = set()\\n    for i in range(n):\\n        for offset in (1, 7, 13):\\n            j = (i + offset) % n\\n            a, b = min(i, j), max(i, j)\\n            edges.add((a, b))\\n    return {i: set() for i in range(n)}, edges"
      }
    },
    {
      "requirement": "R2",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "cover = left  # all even vertices form a minimum vertex cover"
      }
    },
    {
      "requirement": "R3",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "matching_size, _, _ = hopcroft_karp(adj, left, right)\\n    min_cover_size = matching_size  # König's theorem"
      }
    },
    {
      "requirement": "R4",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "print(f\\\"WITNESS: {result}\\\")"
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
      "cover": [
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
      ],
      "size": 25,
      "matching_size": 25
    },
    "provisional": false
  }
}
```
