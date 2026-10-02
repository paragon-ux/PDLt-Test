def LCS(s1: str, s2: str):
    m, n = len(s1), len(s2)
    # DP table of size (m+1) x (n+1)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
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
    return lcs_str, dp[m][n]

# Tests
if __name__ == "__main__":
    tests = [
        ("AGGTAB", "GXTXAYB", "GTAB", 4),
        ("ABC", "ABC", "ABC", 3),
        ("", "ABC", "", 0),
        ("ABC", "DEF", "", 0),
    ]
    all_passed = True
    for s1, s2, expected_lcs, expected_len in tests:
        result_lcs, result_len = LCS(s1, s2)
        if result_lcs != expected_lcs or result_len != expected_len:
            all_passed = False
            print(f"Test failed for s1='{s1}', s2='{s2}': expected ({expected_lcs}, {expected_len}), got ({result_lcs}, {result_len})")
    if all_passed:
        print("All tests passed.")
