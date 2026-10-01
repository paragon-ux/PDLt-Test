The following Python function is slow. Profile it, identify the bottleneck, optimize it, and provide benchmark results comparing before and after.

`python
def find_duplicates(lst):
    duplicates = []
    for i in range(len(lst)):
        for j in range(i + 1, len(lst)):
            if lst[i] == lst[j] and lst[i] not in duplicates:
                duplicates.append(lst[i])
    return sorted(duplicates)

# Test data: 50000 random integers in range [0, 10000]
import random
random.seed(42)
data = [random.randint(0, 10000) for _ in range(50000)]
result = find_duplicates(data)
`

The solution must include: (1) time measurement of the original, (2) explanation of why it's slow (exact big-O), (3) optimized version, (4) time measurement proving the speedup, (5) test proving identical output.
