RUN the First Fit algorithm on the items [5, 5, 5, 3, 3, 3, 7, 7] with bin capacity 10
  CAPTURE the resulting packing as first_fit_packing
SOLVE the bin packing optimization problem for the same items and capacity to obtain an optimal packing
  CAPTURE the optimal packing as optimal_packing
CALCULATE the gap in bin count between first_fit_packing and optimal_packing as gap
REPORT the first_fit_packing
REPORT the optimal_packing
EXPLAIN why the arrival order of items causes the First Fit algorithm to use more bins than the optimal packing
PERFORM a self-test that verifies both packings use all items exactly once and respect the capacity constraint
