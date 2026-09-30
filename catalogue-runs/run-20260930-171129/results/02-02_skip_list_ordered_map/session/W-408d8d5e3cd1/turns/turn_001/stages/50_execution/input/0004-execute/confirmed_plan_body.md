READ the requirements for a skip list implementation with an ordered map interface
DESIGN the skip list node structure including key, value, forward pointers array, and level field
DESIGN the skip list container with maximum level 16 and probability p=0.5
IMPLEMENT the probabilistic level generator using coin‑flip logic
IMPLEMENT insert(key, value) to add new nodes or update existing ones, linking across appropriate levels
IMPLEMENT search(key) to locate a node and return its value or None
IMPLEMENT delete(key) to remove a node and adjust forward links across all levels
IMPLEMENT range_query(lo, hi) to traverse from the lowest relevant level and collect all key‑value pairs satisfying lo ≤ key ≤ hi
GENERATE a comprehensive test suite that exercises insertion ordering, update semantics, search correctness, deletion correctness, and range‑query accuracy
RUN the test suite to verify ordering invariants and functional behavior
INSERT 1000 keys using insert to gather level assignment statistics
MEASURE the distribution of node levels across the 1000 insertions
ANALYZE the measured distribution to confirm it approximates the expected geometric distribution with p=0.5
OUTPUT a summary of test results and level‑distribution verification
