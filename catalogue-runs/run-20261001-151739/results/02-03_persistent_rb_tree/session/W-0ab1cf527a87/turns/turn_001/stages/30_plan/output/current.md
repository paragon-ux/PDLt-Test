DEFINE immutable node structure for persistent red‑black tree.
DEFINE functional INSERT operation that returns a new tree via path copying while preserving immutability.
DEFINE functional LOOKUP operation that checks membership without modifying the tree.
DEFINE functional TO_SORTED_LIST operation that produces an in‑order traversal list.
COMPOSE unit TESTS verifying persistence: after INSERT, confirm original tree remains unchanged.
COMPOSE unit TESTS verifying red‑black invariants: root is black; no red parent has a red child; black‑height is equal on all root‑to‑leaf paths.
COMPOSE unit TESTS verifying binary search tree ordering using TO_SORTED_LIST.
RUN all TESTS and REPORT outcomes.
