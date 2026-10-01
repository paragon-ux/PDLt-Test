IMPLEMENT a Python function that ACCEPTS two input strings s1 and s2
CALCULATE the length of the LCS using dynamic programming
RECONSTRUCT the actual LCS subsequence by backtracking through the DP table
OUTPUT both the length and the subsequence
INCLUDE test cases:
- TEST case 1: WITH s1 = "AGGTAB" AND s2 = "GXTXAYB" EXPECT LCS "GTAB" AND length 4
- TEST case 2: WITH identical strings (e.g., s1 = "HELLO", s2 = "HELLO") EXPECT LCS "HELLO" AND appropriate length
- TEST case 3: WITH one empty string (e.g., s1 = "", s2 = "ANY") EXPECT LCS "" AND length 0
- TEST case 4: WITH strings having no common characters (e.g., s1 = "ABC", s2 = "DEF") EXPECT LCS "" AND length 0
