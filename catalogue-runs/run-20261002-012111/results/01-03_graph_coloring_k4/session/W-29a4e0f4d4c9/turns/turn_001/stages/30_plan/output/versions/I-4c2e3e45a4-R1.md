REPRESENT the wheel graph W_11 with hub node 0 and peripheral nodes 1 through 11 forming a cycle.
IDENTIFY adjacency pairs: hub node 0 adjacent to each peripheral node; each peripheral node i adjacent to i-1 and i+1 (mod 11) forming the peripheral cycle.
SELECT a color for hub node 0 from the set {1,2,3,4}.
ASSIGN colors to peripheral nodes 1‑11 by iterating around the cycle and choosing colors from the set such that no adjacent peripheral nodes share a color and no peripheral node shares the hub’s color.
VALIDATE the coloring by checking every adjacency pair for distinct colors.
OUTPUT the colors assigned to nodes 0, 1, 2, 3, 4, and 11.
NOTE that the peripheral cycle has odd length (11) and therefore requires at least three distinct colors in any proper coloring.
CONSIDER that the hub node is adjacent to all peripheral nodes, which forces any proper coloring to use a fourth distinct color when only three colors are used on the peripheral cycle.
FORMALIZE a proof by contradiction: assume a 3‑coloring exists for W_11, derive that the hub must share a color with some peripheral node, violating adjacency constraints.
CONSTRUCT the contradiction argument using the odd‑cycle property and hub adjacency.
PRESENT the proof that three colors are insufficient, establishing the chromatic number of W_11 as 4.
