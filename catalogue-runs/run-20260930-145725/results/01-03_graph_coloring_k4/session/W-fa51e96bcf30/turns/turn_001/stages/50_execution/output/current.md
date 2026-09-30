UNVERIFIED ANSWER: Substantive verification was not completed after repair attempts. Reason: Substantive verification error: Missing witness in Result IR for task requiring verified execution.

Candidate deliverable:
# Wheel graph W_11 4‑coloring
# Nodes: hub 0, peripheral 1‑11
# Colors: 1,2,3,4
coloring = {
    0: 1,
    1: 2,
    2: 3,
    3: 4,
    4: 2,
    5: 3,
    6: 4,
    7: 2,
    8: 3,
    9: 4,
    10: 2,
    11: 3,
}

# Verification of adjacency constraints
edges = [(0,i) for i in range(1,12)] + [(i,i%11+1) for i in range(1,12)]
assert all(coloring[u] != coloring[v] for u,v in edges), "Invalid coloring"
print("Valid 4‑coloring for W_11:", coloring)

# Proof sketch for impossibility of 3‑coloring (non‑computational):
# The peripheral cycle has odd length 11, requiring at least 3 colors.
# The hub is adjacent to every peripheral node, so its color must differ from all colors used on the cycle.
# Hence a fourth color is necessary.
