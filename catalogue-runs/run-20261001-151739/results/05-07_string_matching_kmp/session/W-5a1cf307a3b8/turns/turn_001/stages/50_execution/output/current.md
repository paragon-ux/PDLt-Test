# KMP implementation with detailed trace for pattern "ABABCABAB"

def build_lps(pattern):
    """Build longest proper prefix which is also suffix (LPS) array.
    Returns the LPS list and prints step-by-step trace.
    """
    m = len(pattern)
    lps = [0] * m
    length = 0  # length of the previous longest prefix suffix
    i = 1
    print(f"Building LPS for pattern: {pattern}")
    print(f"Initial LPS: {lps}")
    while i < m:
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            print(f"i={i}, match: pattern[{i}] == pattern[{length-1}] -> length={length}, lps[{i}]={lps[i]}")
            i += 1
        else:
            if length != 0:
                length = lps[length - 1]
                print(f"i={i}, mismatch: fallback length to lps[{length}] -> {length}")
                # Do not increment i here
            else:
                lps[i] = 0
                print(f"i={i}, mismatch with length=0 -> lps[{i}]=0")
                i += 1
    print(f"Final LPS: {lps}\n")
    return lps

def kmp_search(text, pattern):
    """Search for pattern in text using KMP algorithm.
    Returns list of starting indices where pattern is found.
    """
    n = len(text)
    m = len(pattern)
    lps = build_lps(pattern)
    i = j = 0  # i -> index for text, j -> index for pattern
    matches = []
    print(f"Searching text: {text}\n")
    while i < n:
        if pattern[j] == text[i]:
            i += 1
            j += 1
            if j == m:
                match_pos = i - j
                matches.append(match_pos)
                print(f"Pattern found at index {match_pos}")
                j = lps[j - 1]
        else:
            if j != 0:
                j = lps[j - 1]
                print(f"Mismatch: fallback j to {j}")
            else:
                i += 1
                print(f"Mismatch at start, increment i to {i}")
    print(f"\nAll match positions: {matches}\n")
    return matches

if __name__ == "__main__":
    text = "ABABDAABABCABABABABCABAB"
    pattern = "ABABCABAB"
    positions = kmp_search(text, pattern)
    print("Resulting starting indices:", positions)
