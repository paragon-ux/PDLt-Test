SET bin capacity C TO 10
DEFINE item list AS [5, 5, 5, 3, 3, 3, 7, 7]
APPLY First Fit algorithm TO the item list USING bins OF capacity C
REPORT the packing produced BY First Fit
COMPUTE an optimal bin-packing THAT minimizes the number OF bins FOR the same item list AND bin capacity C
REPORT the optimal packing
CALCULATE the difference IN number OF bins BETWEEN the First Fit packing AND the optimal packing
EXPLAIN why the arrival order OF items causes First Fit TO use more bins THAN the optimal solution
PERFORM a self-test THAT verifies EACH packing INCLUDES every item EXACTLY once AND that NO bin EXCEEDS capacity C
