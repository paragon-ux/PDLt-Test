DEFINE S = {3, 34, 7, 12, 5, 26, 11, 8, 15, 2, 19, 21}
DEFINE T = 40
USE a backtracking algorithm to explore the full search tree of subsets of S
  FOR each candidate subset generated
    IF the sum of the subset equals T
      EMIT the subset
      VERIFY that the subset sum equals T
COUNT the emitted subsets
REPORT the total number of solutions
