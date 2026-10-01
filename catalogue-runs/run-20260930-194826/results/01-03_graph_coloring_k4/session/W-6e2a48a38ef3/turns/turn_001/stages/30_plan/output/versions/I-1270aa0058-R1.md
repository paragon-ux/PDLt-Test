DEFINE the wheel graph W_11 with central node 0 and peripheral nodes 1 through 11 forming an odd cycle
VERIFY adjacency relationships: node 0 adjacent to all peripheral nodes; each peripheral node i adjacent to i-1 and i+1 modulo 11
ATTEMPT a 3‑color assignment for the peripheral odd cycle
IF a proper 3‑coloring exists for the cycle THEN note that the hub node would share a color with at least one peripheral neighbor, violating adjacency constraints
ELSE conclude that a 3‑coloring is impossible for the combined graph
PROCEED to construct a valid 4‑color assignment:
    ASSIGN colors to peripheral nodes in a repeating pattern of three colors (e.g., 1,2,3,1,2,3,1,2,3,1,2) ensuring no adjacent peripheral nodes share a color
    IDENTIFY any peripheral node whose color matches the hub’s color
    SELECT a fourth color for the hub (color 4) distinct from all peripheral colors
OUTPUT the final coloring mapping for nodes 0 through 11
