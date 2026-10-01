RUN First Fit algorithm on the given item sequence with bin capacity 10 and OUTPUT the resulting packing.
DETERMINE an optimal packing that minimizes the number of bins for the same items and OUTPUT that packing.
CALCULATE the numeric difference in bin count between the First Fit result and the optimal result and OUTPUT the gap.
EXPLAIN why the arrival order causes First Fit to use more bins than the optimal packing.\nSELF-TEST:
    VERIFY that both packings include every item exactly once.
    VERIFY that the total size of items in each bin does not exceed the capacity of 10.
    VERIFY that the optimal packing uses the minimal possible number of bins for the given items.
