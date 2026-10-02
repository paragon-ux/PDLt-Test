SET bin capacity C = 10
DEFINE item list as [5, 5, 5, 3, 3, 3, 7, 7]
APPLY First Fit algorithm to the item list using bins of capacity C = 10
REPORT the resulting packing from First Fit
COMPUTE an optimal bin‑packing that minimizes the number of bins for the same item list and bin capacity
REPORT the optimal packing
CALCULATE the gap between the number of bins used by First Fit and the number used by the optimal packing
EXPLAIN why the arrival order of items leads First Fit to use more bins than the optimal solution
INCLUDE a self‑test that verifies both packings include each item exactly once and that no bin exceeds capacity C = 10
