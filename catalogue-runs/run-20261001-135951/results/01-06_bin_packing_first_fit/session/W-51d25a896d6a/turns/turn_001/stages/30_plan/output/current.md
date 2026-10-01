RUN First Fit algorithm on items [5,5,5,3,3,3,7,7] with bin capacity 10
REPORT resulting packing
FIND optimal packing minimizing number of bins for same items and capacity
REPORT optimal packing
CALCULATE gap between number of bins used by First Fit result and optimal result
REPORT gap
EXPLAIN why arrival order causes First Fit to use more bins than optimal solution
VERIFY that both packings use all items exactly once
VERIFY that each bin in both packings respects capacity constraint of 10
