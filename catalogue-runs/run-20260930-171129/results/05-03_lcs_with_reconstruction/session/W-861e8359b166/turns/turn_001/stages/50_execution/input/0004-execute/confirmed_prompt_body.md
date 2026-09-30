READ two input strings s1 and s2.
COMPUTE a dynamic programming table to determine the length of the longest common subsequence (LCS) between s1 and s2.
BACKTRACK through the DP table to reconstruct the actual LCS subsequence.
OUTPUT the length of the LCS and the reconstructed subsequence.
PROVIDE tests:
- TEST with s1 = "AGGTAB" and s2 = "GXTXAYB" expecting LCS "GTAB" of length 4.
- TEST with identical strings to verify the LCS equals the full string.
- TEST with one empty string to verify LCS length 0 and empty subsequence.
- TEST with strings having no common characters to verify LCS length 0 and empty subsequence.
INCLUDE the operative task entities: LCS, Python, dynamic programming, s1, s2, AGGTAB, GXTXAYB, GTAB, 4.
