READ the input strings s1 and s2
INITIALIZE a DP table for LCS dimensions (len(s1)+1) by (len(s2)+1)
FILL the DP table using the LCS dynamic programming recurrence
COMPUTE the LCS length from the DP table entry at (len(s1), len(s2))
BACKTRACK through the DP table to reconstruct the LCS subsequence
OUTPUT the LCS length and subsequence
VALIDATE implementation with test cases:
    - EXECUTE the algorithm with s1 = "AGGTAB", s2 = "GXTXAYB"
    - EXECUTE the algorithm with s1 = "hello", s2 = "hello"
    - EXECUTE the algorithm with s1 = "", s2 = "any"
    - EXECUTE the algorithm with s1 = "ABC", s2 = "DEF"
