DEFINE the set of colors {1,2,3,4}
FOR each node in the wheel graph W_11 (nodes 0 through 11)
ASSIGN a color from the set ensuring:
IF node is 0 (hub) THEN its color differs from colors of all rim nodes 1‑11
IF node is a rim node i (1‑11) THEN its color differs from the hub (node 0) and from its two adjacent rim neighbors (i‑1 and i+1, with wrap‑around for 11 and 1)
VERIFY that the resulting assignment satisfies all adjacency constraints
FOR the impossibility proof with only three colors
ANALYZE the parity of the rim cycle (11 nodes, odd length) to show that a proper 3‑coloring of the cycle forces the hub to share a color with at least one rim node
CONCLUDE that a fourth distinct color is required
OUTPUT the complete color assignment for nodes 0‑11
OUTPUT a brief justification summarizing the parity argument that rules out a three‑color solution
