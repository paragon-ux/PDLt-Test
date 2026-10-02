ENTITIES: s1, s2, AGGTAB, GXTXAYB, GTAB, 4
IMPLEMENT a Python function LCS(s1, s2) that computes the longest common subsequence using dynamic programming.
BUILD a DP table of LCS lengths for s1 and s2.
BACKTRACK through the DP table from the bottom-right corner to reconstruct the LCS string.
RETURN both the LCS string and its length.
INCLUDE tests:
    TEST with s1 = "AGGTAB" and s2 = "GXTXAYB" expects LCS "GTAB" and length 4.
    TEST with identical strings such as s1 = "ABC" and s2 = "ABC" expects LCS "ABC" and length 3.
    TEST with one empty string such as s1 = "" and s2 = "ABC" expects LCS "" and length 0.
    TEST with strings having no common characters such as s1 = "ABC" and s2 = "DEF" expects LCS "" and length 0.
