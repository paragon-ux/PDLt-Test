SET bin capacity C to 10
RUN First Fit algorithm on items [5, 5, 5, 3, 3, 3, 7, 7] with capacity C
    RECORD the resulting packing
REPORT the First Fit packing
COMPUTE an optimal packing that minimizes the number of bins for the same items and capacity
    RECORD the optimal packing
REPORT the optimal packing
CALCULATE the gap between the number of bins used by First Fit and the optimal packing
    RECORD the gap
REPORT the gap
EXPLAIN why the given arrival order causes First Fit to use more bins
PERFORM a SELF-TEST that verifies both packings use all items exactly once and respect the capacity constraint
