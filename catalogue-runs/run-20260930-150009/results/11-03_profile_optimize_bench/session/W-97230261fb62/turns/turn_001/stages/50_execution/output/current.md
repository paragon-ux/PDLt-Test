import random, time

def find_duplicates(lst):
    """Original O(n^2) implementation that returns a sorted list of duplicate values."""
    duplicates = []
    for i in range(len(lst)):
        for j in range(i + 1, len(lst)):
            if lst[i] == lst[j] and lst[i] not in duplicates:
                duplicates.append(lst[i])
    return sorted(duplicates)

def find_duplicates_optimized(lst):
    """Optimized O(n) implementation using a hash map to track occurrences."""
    from collections import Counter
    counts = Counter(lst)
    # keep values that appear more than once, then sort
    return sorted([val for val, cnt in counts.items() if cnt > 1])

# generate test data: 50000 random integers in [0, 10000]
random.seed(42)
data = [random.randint(0, 10000) for _ in range(50000)]

# measure original
start = time.perf_counter()
orig_result = find_duplicates(data)
orig_time = time.perf_counter() - start
print(f"Original function time: {orig_time:.6f} seconds")

# measure optimized
start = time.perf_counter()
opt_result = find_duplicates_optimized(data)
opt_time = time.perf_counter() - start
print(f"Optimized function time: {opt_time:.6f} seconds")

# verify identical sorted output
assert orig_result == opt_result, "Results differ!"
print("Verification passed: both functions produce identical sorted duplicate output.")
