# Wrong: resets to zero after a match, so overlapping occurrences are missed.
def build_failure(pattern):
    fail, k = [0] * len(pattern), 0
    for i in range(1, len(pattern)):
        while k and pattern[i] != pattern[k]:
            k = fail[k - 1]
        if pattern[i] == pattern[k]:
            k += 1
        fail[i] = k
    return fail


def kmp_search(text, pattern):
    fail, out, k = build_failure(pattern), [], 0
    for i, ch in enumerate(text):
        while k and ch != pattern[k]:
            k = fail[k - 1]
        if ch == pattern[k]:
            k += 1
        if k == len(pattern):
            out.append(i - k + 1)
            k = 0
    return out
