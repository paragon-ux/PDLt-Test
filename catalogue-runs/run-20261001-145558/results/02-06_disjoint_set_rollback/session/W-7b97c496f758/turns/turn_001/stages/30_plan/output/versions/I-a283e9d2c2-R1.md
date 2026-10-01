DESIGN a disjoint‑set data structure using union‑by‑rank without path compression
IMPLEMENT make_set(x) to create a singleton set with initial rank 0
IMPLEMENT find(x) to return the representative by following parent links
IMPLEMENT union(x, y) to merge two sets based on rank, updating parent and rank
IMPLEMENT save() to push a snapshot of the current parent and rank arrays onto a stack
IMPLEMENT restore() to pop the most recent snapshot and replace the current arrays, reverting all unions performed since the last save
WRITE unit tests that
    VERIFY basic make_set, find, and union correctness
    CALL save(), perform unions, then CALL restore() and ASSERT that the component structure matches the state before the unions
    NEST multiple save/restore calls and ASSERT correct restoration after each restore
