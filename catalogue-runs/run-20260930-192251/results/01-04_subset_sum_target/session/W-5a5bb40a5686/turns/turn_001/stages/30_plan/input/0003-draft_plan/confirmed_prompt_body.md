READ the set S = {3, 34, 7, 12, 5, 26, 11, 8, 15, 2, 19, 21}
READ the target sum T = 40
FIND all subsets of S whose elements sum exactly to T using a backtracking search that explores the full search tree
FOR each element in S decide to INCLUDE it in the current subset or EXCLUDE it
MAINTAIN the running sum of the current subset
PRUNE any branch where the running sum exceeds T
WHEN the running sum equals T EMIT the current subset as a solution
VERIFY that the emitted subset sums to T
COUNT each emitted subset and REPORT the total number of solutions found
