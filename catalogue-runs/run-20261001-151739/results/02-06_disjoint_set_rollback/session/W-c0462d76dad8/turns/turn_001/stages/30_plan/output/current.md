READ the request for a union-find data structure with rollback support in Python.
DEFINE a UnionFindRollback class encapsulating parent, rank, and a history stack.
IMPLEMENT make_set(x) to initialize a new element as its own parent with rank zero.
IMPLEMENT find(x) to traverse parent pointers and return the set representative without path compression.
IMPLEMENT union(x, y) to merge the sets containing x and y using union‑by‑rank.
IMPLEMENT save() to record a snapshot of the current parent and rank arrays onto the history stack.
IMPLEMENT restore() to revert to the most recent snapshot by popping from the history stack and restoring parent and rank.
WRITE unit tests that create singleton sets, perform unions, and verify find returns correct representatives.
WRITE unit tests that invoke save(), perform unions, call restore(), and verify the component structure matches the state prior to the unions.
WRITE unit tests that perform multiple nested save() calls, execute unions between saves, restore sequentially, and verify the structure after each restore matches the expected prior state.
EXECUTE the test suite to ensure all assertions pass.
