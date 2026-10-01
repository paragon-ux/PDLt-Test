```python
import random, time

def find_duplicates(lst):
    duplicates = []
    for i in range(len(lst)):
        for j in range(i + 1, len(lst)):
            if lst[i] == lst[j] and lst[i] not in duplicates:
                duplicates.append(lst[i])
    return sorted(duplicates)

def find_duplicates_optimized(lst):
    seen = set()
    duplicates = set()
    for item in lst:
        if item in seen:
            duplicates.add(item)
        else:
            seen.add(item)
    return sorted(duplicates)

# Prepare test data
random.seed(42)
data = [random.randint(0, 10000) for _ in range(50000)]

# Measure original version
start = time.time()
orig_result = find_duplicates(data)
orig_time = time.time() - start

# Measure optimized version
start = time.time()
opt_result = find_duplicates_optimized(data)
opt_time = time.time() - start

# Verify identical output
assert orig_result == opt_result, "Outputs differ"

print(f"Original time: {orig_time:.4f} seconds")
print(f"Optimized time: {opt_time:.4f} seconds")
print(f"Speedup: {orig_time/opt_time:.2f}x")
```
