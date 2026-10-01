# LCS implementation using dynamic programming

def lcs(s1: str, s2: str):
    """Return a tuple (length, subsequence) of the longest common subsequence of s1 and s2."""
    m, n = len(s1), len(s2)
    # DP table where dp[i][j] is length of LCS of s1[:i] and s2[:j]
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
    subsequence = ''.join(reversed(lcs_chars))
    return dp[m][n], subsequence

# Test cases
if __name__ == "__main__":
    tests = [
        ("AGGTAB", "GXTXAYB", "GTAB", 4),
        ("hello", "hello", "hello", 5),
        ("", "any", "", 0),
        ("ABC", "DEF", "", 0),
    ]
    for s1, s2, expected_seq, expected_len in tests:
        length, seq = lcs(s1, s2)
        assert length == expected_len, f"Length mismatch for {s1!r}, {s2!r}: {length} != {expected_len}"
        assert seq == expected_seq, f"Seq mismatch for {s1!r}, {s2!r}: {seq!r} != {expected_seq!r}"
    print("All tests passed.")
