PROFILE the Python function find_duplicates that takes list lst and returns a sorted list of duplicates.
IDENTIFY the performance bottleneck (nested loops using i, range, len causing O(n^2) complexity).
EXPLAIN why the bottleneck is slow.
PRODUCE an optimized implementation of find_duplicates using a set or dictionary to achieve O(n) time.
MEASURE execution time of both the original implementation and the optimized implementation on data of 50000 random integers in the range [0,10000] with random seed 42.
PRESENT benchmark results showing the speedup.
VERIFY that both implementations produce identical result.
