DESIGN a UnionFind class supporting union-by-rank
DEFINE internal structures: a dictionary parent mapping each element to its representative, a dictionary rank storing tree depths, and a stack history to record state changes for rollback
IMPLEMENT make_set(x) to initialize parent[x] = x and rank[x] = 0
IMPLEMENT find(x) to follow parent links until the representative is reached (no path compression)
IMPLEMENT union(x, y) to locate representatives rx and ry via find; IF rx ≠ ry THEN
COMPARE rank[rx] and rank[ry]
ATTACH the lower‑rank tree under the higher‑rank tree
IF ranks are equal, increment the rank of the new root
PUSH a record onto history capturing the affected element, its previous parent, and previous rank values
DEFINE save() to push a marker onto history indicating a save point
DEFINE restore() to pop history entries until the most recent save marker is removed, reverting each popped entry’s parent and rank to the stored previous values
WRITE unit tests that:
CREATE a UnionFind instance
CALL make_set for multiple elements
PERFORM unions and verify find returns expected representatives
CALL save(), execute additional unions, then CALL restore() and verify the structure reverts to the state captured at save
NEST multiple save/restore sequences and assert correct rollback behavior at each level
