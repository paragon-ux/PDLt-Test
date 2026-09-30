# KMP implementation with detailed trace for pattern "ABABCABAB"

def build_failure_function(pattern: str):
    """Builds the failure (partial match) table for the given pattern.
    Returns a list where pi[i] is the length of the longest proper prefix of
    pattern[:i+1] which is also a suffix of this substring.
    Also prints a step‑by‑step trace of the construction."""
    m = len(pattern)
    pi = [0] * m
    k = 0
    print("Failure function construction trace:")
    print(f"i=0 ({pattern[0]}): pi[0]=0")
    for i in range(1, m):
        while k > 0 and pattern[k] != pattern[i]:
            print(f"  mismatch at i={i} ({pattern[i]}), k={k} ({pattern[k]}). fallback to pi[{k-1}]={pi[k-1]}")
            k = pi[k-1]
        if pattern[k] == pattern[i]:
            k += 1
            print(f"  match at i={i} ({pattern[i]}), increment k to {k}")
        else:
            print(f"  no match at i={i} ({pattern[i]}), k stays {k}")
        pi[i] = k
        print(f"i={i} ({pattern[i]}): pi[{i}]={pi[i]}")
    print("Final failure function:", pi)
    return pi

def kmp_search(text: str, pattern: str):
    """Searches for all occurrences of pattern in text using KMP.
    Returns a list of starting indices (0‑based)."""
    pi = build_failure_function(pattern)
    n, m = len(text), len(pattern)
    q = 0  # number of characters matched
    result = []
    for i in range(n):
        while q > 0 and pattern[q] != text[i]:
            q = pi[q-1]
        if pattern[q] == text[i]:
            q += 1
        if q == m:
            result.append(i - m + 1)
            q = pi[q-1]
    return result

if __name__ == "__main__":
    text = "ABABDAABABCABABABABCABAB"
    pattern = "ABABCABAB"
    matches = kmp_search(text, pattern)
    print("Match positions (0‑based):", matches)
