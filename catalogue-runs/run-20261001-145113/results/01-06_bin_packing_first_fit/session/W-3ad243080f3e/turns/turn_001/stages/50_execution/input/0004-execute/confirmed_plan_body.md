READ bin capacity C = 10
READ items list Items = [5,5,5,3,3,3,7,7]
APPLY First Fit algorithm to Items with capacity C in arrival order and STORE packing as FF_PACKING
DETERMINE optimal packing of Items with capacity C that minimizes number of bins and STORE as OPTIMAL_PACKING
CALCULATE gap between FF_PACKING and OPTIMAL_PACKING and STORE as GAP
EXPLAIN why the arrival order causes First Fit to use more bins and STORE as EXPLANATION
SELF-TEST that both packings use each item exactly once and each bin respects capacity C, and STORE results as SELF_TEST_RESULTS
REPORT FF_PACKING, OPTIMAL_PACKING, GAP, EXPLANATION, SELF_TEST_RESULTS
