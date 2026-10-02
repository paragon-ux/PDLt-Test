TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Profile the provided Python function `find_duplicates` that takes a list `lst` and returns a sorted list of duplicate values. Identify its performance bottleneck (nested loops causing O(n^2) complexity), explain why it is slow, produce an optimized implementation (e.g., using a set or dictionary to achieve O(n) time), measure execution time of both the original and optimized versions on a dataset of 50000 random integers in the range [0,10000] (random seed 42), present benchmark results showing the speedup, and verify that both implementations produce identical output.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- find_duplicates
- lst
- duplicates
- i
- range
- len
- sorted
- random
- seed
- 42
- data
- 50000
- 10000
- result
