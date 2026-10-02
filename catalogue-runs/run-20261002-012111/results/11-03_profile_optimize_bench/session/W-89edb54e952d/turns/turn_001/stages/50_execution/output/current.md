import random, time

# Original implementation (O(n^2))
def find_duplicates_original(lst):
    duplicates = []
    n = len(lst)
    for i in range(n):
        for j in range(i + 1, n):
            if lst[i] == lst[j] and lst[i] not in duplicates:
                duplicates.append(lst[i])
    return sorted(duplicates)

# Optimized implementation (O(n)) using a set
def find_duplicates_optimized(lst):
    seen = set()
    dup_set = set()
    for item in lst:
        if item in seen:
            dup_set.add(item)
        else:
            seen.add(item)
    return sorted(dup_set)

# Prepare test data
random.seed(42)
data = [random.randint(0, 10000) for _ in range(50000)]

# Measure original implementation
start_orig = time.perf_counter()
orig_result = find_duplicates_original(data)
end_orig = time.perf_counter()
orig_time = end_orig - start_orig

# Measure optimized implementation
start_opt = time.perf_counter()
opt_result = find_duplicates_optimized(data)
end_opt = time.perf_counter()
opt_time = end_opt - start_opt

# Verify identical output
assert orig_result == opt_result, "Results differ!"

# Print benchmark results
print(f"Original implementation time: {orig_time:.6f} seconds")
print(f"Optimized implementation time: {opt_time:.6f} seconds")
print(f"Speedup: {orig_time / opt_time:.2f}x")
