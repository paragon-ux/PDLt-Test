DEFINE a Python class to implement union-find with rollback support
INITIALIZE data structures for parent pointers, rank values, and a history stack
IMPLEMENT make_set(x) to create a singleton set with rank zero
IMPLEMENT find(x) to return the representative of x without path compression
IMPLEMENT union(x, y) to merge the sets containing x and y using union-by-rank, recording the operation for possible rollback
IMPLEMENT save() to capture a snapshot of the current parent and rank structures and push it onto the history stack
IMPLEMENT restore() to pop the most recent snapshot from the history stack and revert the parent and rank structures to that state
DEVISE a test suite that verifies basic union-find correctness for make_set, find, and union operations
DEVISE a test suite that verifies rollback behavior by performing unions, invoking save, performing additional unions, invoking restore, and checking that the structure matches the saved state
DEVISE a test suite that verifies nested save/restore sequences with multiple saves and restores interleaved with unions
LIST the following task entities verbatim: union-find, disjoint set, Python, union-by-rank, no path compression, make_set(x), find(x), union(x, y), save(), restore().
