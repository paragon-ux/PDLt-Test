PREPARE the inputs s1 and s2.
BUILD a DP table of LCS lengths for s1 and s2 using bottom‑up dynamic programming.
BACKTRACK through the DP table from the bottom‑right corner to reconstruct the LCS string.
RETURN both the LCS string and its length.
EXECUTE the defined tests:
    TEST with s1 = "AGGTAB" and s2 = "GXTXAYB" expects LCS "GTAB" and length 4.
    TEST with s1 = "ABC" and s2 = "ABC" expects LCS "ABC" and length 3.
    TEST with s1 = "" and s2 = "ABC" expects LCS "" and length 0.
    TEST with s1 = "ABC" and s2 = "DEF" expects LCS "" and length 0.
