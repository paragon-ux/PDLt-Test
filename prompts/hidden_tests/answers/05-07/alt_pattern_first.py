# Correct with a different interface: (pattern, text) order, a generator, and no
# exposed failure-function name from the list.
def _table(p):
    t = [0] * len(p)
    j = 0
    for i in range(1, len(p)):
        while j > 0 and p[i] != p[j]:
            j = t[j - 1]
        if p[i] == p[j]:
            j += 1
        t[i] = j
    return t


def find_all(pattern, text):
    table, j = _table(pattern), 0
    for i, c in enumerate(text):
        while j > 0 and c != pattern[j]:
            j = table[j - 1]
        if c == pattern[j]:
            j += 1
        if j == len(pattern):
            yield i - len(pattern) + 1
            j = table[j - 1]
