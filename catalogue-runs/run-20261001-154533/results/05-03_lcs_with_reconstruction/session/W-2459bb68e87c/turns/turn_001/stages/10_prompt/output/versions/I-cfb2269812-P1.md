READ the input strings s1 and s2
IMPLEMENT the LCS algorithm in Python using dynamic programming
CALCULATE the DP table for LCS (DP) using dynamic programming
COMPUTE the length of the LCS from the DP table
RECONSTRUCT the LCS subsequence by backtracking through the DP table
OUTPUT the length and the subsequence
INCLUDE test cases:
    - s1 = "AGGTAB", s2 = "GXTXAYB" => expected LCS "GTAB" of length 4
    - identical strings (e.g., s1 = "hello", s2 = "hello") => expected LCS "hello" of length 5
    - one empty string (e.g., s1 = "", s2 = "any") => expected LCS "" of length 0
    - strings with no common characters (e.g., s1 = "ABC", s2 = "DEF") => expected LCS "" of length 0
