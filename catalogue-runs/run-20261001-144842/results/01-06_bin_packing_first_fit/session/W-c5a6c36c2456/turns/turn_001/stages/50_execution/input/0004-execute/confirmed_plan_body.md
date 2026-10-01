DEFINE item sequence as [5, 5, 5, 3, 3, 3, 7, 7].
DEFINE bin capacity as 10.
APPLY First Fit algorithm to the sequence, ASSIGN items to bins, RECORD bin contents.
LIST each bin's contents for the First Fit packing.
APPLY optimal bin packing algorithm to the sequence, MINIMIZE number of bins, RECORD bin contents.
LIST each bin's contents for the optimal packing.
CALCULATE the difference in bin count between the First Fit result and the optimal result.
ANALYZE why the given arrival order causes First Fit to use more bins, GENERATE explanation.
CONSTRUCT self-test that VERIFIES both packings contain each item exactly once and that no bin exceeds capacity 10.
EXECUTE the self-test and RECORD verification outcomes.
OUTPUT the First Fit bin listing, optimal bin listing, bin count difference, explanation of order effect, and self-test verification results.
