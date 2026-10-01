```python
def build_failure_function(pattern):
    """Construct the failure (partial match) table for KMP.
    Returns a list where table[i] is the length of the longest proper prefix
    of pattern[:i+1] that is also a suffix of this substring.
    """
    m = len(pattern)
    table = [0] * m
    j = 0  # length of the previous longest prefix suffix
    # Start from the second character (i=1)
    for i in range(1, m):
        while j > 0 and pattern[i] != pattern[j]:
            j = table[j-1]
        if pattern[i] == pattern[j]:
            j += 1
            table[i] = j
        else:
            table[i] = 0
    return table

def kmp_search(text, pattern):
    """Yield starting indices of pattern occurrences in text using KMP."""
    n, m = len(text), len(pattern)
    if m == 0:
        return []
    table = build_failure_function(pattern)
    i = j = 0
    results = []
    while i < n:
        if text[i] == pattern[j]:
            i += 1
            j += 1
            if j == m:
                results.append(i - m)
                j = table[j-1]
        else:
            if j != 0:
                j = table[j-1]
            else:
                i += 1
    return results

if __name__ == "__main__":
    pattern = "ABABCABAB"
    text = "ABABDAABABCABABABABCABAB"
    # Step‑by‑step construction of failure function
    print("Failure function construction trace:")
    ft = build_failure_function(pattern)
    print("Pattern:", pattern)
    print("Failure table:", ft)
    # Perform search
    matches = kmp_search(text, pattern)
    print("Match positions (0‑based indices):", matches)
    # Verification
    for pos in matches:
        assert text[pos:pos+len(pattern)] == pattern
    print("All matches verified.")
```
