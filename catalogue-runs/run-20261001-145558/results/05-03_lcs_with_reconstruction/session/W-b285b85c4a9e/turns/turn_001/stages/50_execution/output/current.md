def lcs(s1: str, s2: str):
    """Return length and one LCS of s1 and s2 using dynamic programming.
    The subsequence is reconstructed by backtracking through the DP table.
    """
    m, n = len(s1), len(s2)
    # DP table of size (m+1) x (n+1)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    # Reconstruct LCS
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

# Test cases
if __name__ == "__main__":
    tests = [
        ("AGGTAB", "GXTXAYB", 4, "GTAB"),
        ("ABCDEF", "ABCDEF", 6, "ABCDEF"),
        ("", "XYZ", 0, ""),
        ("XYZ", "", 0, ""),
        ("ABC", "DEF", 0, "")
    ]
    for s1, s2, exp_len, exp_seq in tests:
        length, seq = lcs(s1, s2)
        assert length == exp_len, f"Length mismatch for {s1},{s2}: {length} != {exp_len}"
        assert seq == exp_seq, f"Sequence mismatch for {s1},{s2}: {seq} != {exp_seq}"
    print("All tests passed.")
