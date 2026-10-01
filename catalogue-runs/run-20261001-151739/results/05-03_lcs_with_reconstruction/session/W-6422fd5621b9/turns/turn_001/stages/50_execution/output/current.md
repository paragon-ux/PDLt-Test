def LCS(s1: str, s2: str):
    """Return a tuple (length, subsequence) of the longest common subsequence of s1 and s2.
    Uses dynamic programming with backtracking to reconstruct the subsequence.
    """
    m, n = len(s1), len(s2)
    # DP table of size (m+1) x (n+1)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = dp[i - 1][j] if dp[i - 1][j] >= dp[i][j - 1] else dp[i][j - 1]
    # Backtrack to get LCS string
    i, j = m, n
    lcs_chars = []
    while i > 0 and j > 0:
        if s1[i - 1] == s2[j - 1]:
            lcs_chars.append(s1[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    lcs_str = ''.join(reversed(lcs_chars))
    return dp[m][n], lcs_str

# Test suite
if __name__ == "__main__":
    tests = [
        ("AGGTAB", "GXTXAYB", "GTAB", 4),
        ("HELLO", "HELLO", "HELLO", 5),
        ("", "ANY", "", 0),
        ("ABC", "DEF", "", 0),
    ]
    for idx, (s1, s2, exp_seq, exp_len) in enumerate(tests, 1):
        length, seq = LCS(s1, s2)
        ok = (length == exp_len and seq == exp_seq)
        print(f"Test {idx}: {'PASS' if ok else 'FAIL'} - got (len={length}, seq='{seq}') expected (len={exp_len}, seq='{exp_seq}')")
