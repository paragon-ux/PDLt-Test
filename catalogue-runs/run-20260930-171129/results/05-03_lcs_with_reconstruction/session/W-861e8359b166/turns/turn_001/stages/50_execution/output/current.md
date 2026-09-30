import sys

def lcs(s1: str, s2: str):
    m, n = len(s1), len(s2)
    # DP table
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    # backtrack
    i, j = m, n
    subseq = []
    while i > 0 and j > 0:
        if s1[i - 1] == s2[j - 1]:
            subseq.append(s1[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    return dp[m][n], ''.join(reversed(subseq))

def run_tests():
    tests = [
        ("AGGTAB", "GXTXAYB", "GTAB", 4),
        ("HELLO", "HELLO", "HELLO", 5),
        ("", "ANY", "", 0),
        ("ABC", "DEF", "", 0),
    ]
    for s1, s2, exp_seq, exp_len in tests:
        length, seq = lcs(s1, s2)
        assert length == exp_len, f"Length mismatch for {s1!r},{s2!r}: got {length}, expected {exp_len}"
        assert seq == exp_seq, f"Seq mismatch for {s1!r},{s2!r}: got {seq!r}, expected {exp_seq!r}"
    print("All tests passed.")

if __name__ == "__main__":
    # Example execution
    s1 = "AGGTAB"
    s2 = "GXTXAYB"
    length, seq = lcs(s1, s2)
    print(f"LCS length: {length}")
    print(f"LCS subsequence: {seq}")
    # Run verification tests
    run_tests()
