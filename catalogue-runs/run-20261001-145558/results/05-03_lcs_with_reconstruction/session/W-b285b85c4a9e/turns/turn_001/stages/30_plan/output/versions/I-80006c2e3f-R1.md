VALIDATE that two input strings s1 and s2 are provided
INITIALIZE a two-dimensional DP table of size (len(s1)+1) by (len(s2)+1) with zeros
FOR each character index i from 1 to len(s1)
    FOR each character index j from 1 to len(s2)
        IF s1[i-1] equals s2[j-1]
            SET DP[i][j] to DP[i-1][j-1] plus one
        ELSE
            SET DP[i][j] to the maximum of DP[i-1][j] and DP[i][j-1]
ENDFOR
ENDFOR
BACKTRACK from DP[len(s1)][len(s2)] to reconstruct the LCS subsequence
OUTPUT the length of the LCS and the reconstructed subsequence
EXECUTE test case s1 = "AGGTAB", s2 = "GXTXAYB" expecting length 4 and subsequence "GTAB"
EXECUTE additional test cases for identical strings, one empty string, and no common characters
