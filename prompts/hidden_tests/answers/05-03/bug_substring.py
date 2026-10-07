# Wrong: computes the longest common SUBSTRING (contiguous), not subsequence.
def lcs(s1, s2):
    best, end = 0, 0
    dp = [[0] * (len(s2) + 1) for _ in range(len(s1) + 1)]
    for i in range(1, len(s1) + 1):
        for j in range(1, len(s2) + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                if dp[i][j] > best:
                    best, end = dp[i][j], i
    return best, s1[end - best:end]
