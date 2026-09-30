READ the input strings s1 and s2
INITIALIZE a DP table of size (len(s1)+1) x (len(s2)+1) with zeros
FOR i FROM 1 TO len(s1)
FOR j FROM 1 TO len(s2)
IF s1[i-1] == s2[j-1]
SET DP[i][j] = DP[i-1][j-1] + 1
ELSE
SET DP[i][j] = MAX(DP[i-1][j], DP[i][j-1])
ENDIF
ENDFOR
ENDFOR
BACKTRACK from DP[len(s1)][len(s2)] to reconstruct the LCS sequence
OUTPUT the length of the LCS and the reconstructed subsequence
EXECUTE test case: s1 = "AGGTAB", s2 = "GXTXAYB", expect LCS "GTAB" length 4
EXECUTE test case: identical strings, expect LCS equal to full string
EXECUTE test case: one empty string, expect length 0 and empty subsequence
EXECUTE test case: strings with no common characters, expect length 0 and empty subsequence
