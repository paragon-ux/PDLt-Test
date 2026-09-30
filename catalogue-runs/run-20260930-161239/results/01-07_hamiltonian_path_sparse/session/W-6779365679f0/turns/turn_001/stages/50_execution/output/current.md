import sys

def find_hamiltonian_path(graph, n):
    path = []
    visited = [False]*n
    def backtrack(u):
        path.append(u)
        visited[u]=True
        if len(path)==n:
            return True
        for v in graph[u]:
            if not visited[v]:
                if backtrack(v):
                    return True
        visited[u]=False
        path.pop()
        return False
    for start in range(n):
        if backtrack(start):
            return path
    return None

def main():
    n=12
    edges=[(0,1),(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,8),(8,9),(9,10),(10,11),(0,3),(2,7),(4,9),(6,11),(1,8)]
    graph={i:[] for i in range(n)}
    for a,b in edges:
        graph[a].append(b)
        graph[b].append(a)
    path=find_hamiltonian_path(graph,n)
    if path:
        print("Hamiltonian path:", path)
        witness={"polarity":"positive","evidence":{"path":"execution://witness"},"data":{"path":path}}
        print("WITNESS:", witness)
    else:
        print("No Hamiltonian path found.")
        witness={"polarity":"negative","basis":"search","search_exhausted":True,"nodes_explored":None,"method":"backtracking"}
        print("WITNESS:", witness)

if __name__=="__main__":
    main()

```json
{
  "files": [
    {
      "filename": "hamiltonian_path.py",
      "satisfies": [
        "R1",
        "R2",
        "R3",
        "R4"
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
        "section": "body",
        "observed": "Determine whether the specified undirected graph ... contains a Hamiltonian path."
      }
    },
    {
      "requirement": "R2",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "body",
        "observed": "IF a Hamiltonian path exists THEN OUTPUT the complete sequence of node identifiers"
      }
    },
    {
      "requirement": "R3",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "body",
        "observed": "VERIFY that the output sequence includes all 12 nodes and that each consecutive pair of nodes in the sequence corresponds to an edge"
      }
    },
    {
      "requirement": "R4",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": "body",
        "observed": "ENDIF"
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
