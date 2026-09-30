DEFINE the wheel graph W_11 with 12 nodes (central hub 0, outer cycle nodes 1‑11)
GENERATE a 4‑color assignment for all nodes such that each edge connects nodes of different colors
VERIFY that the outer cycle (odd length) uses at least three colors
VERIFY that the hub node is colored differently from each of its adjacent outer nodes
COMPOSE the final output as a list of (node, color) pairs
PREPARE an explanatory argument that a 3‑coloring cannot exist because the odd outer cycle requires three colors and the hub, adjacent to all outer nodes, would share a color with one of them, violating proper coloring
EMIT the node‑color list and the impossibility explanation
