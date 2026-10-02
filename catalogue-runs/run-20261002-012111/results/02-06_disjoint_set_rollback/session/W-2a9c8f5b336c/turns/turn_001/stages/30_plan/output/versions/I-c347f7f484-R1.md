DESIGN a disjoint-set data structure with parent pointers and rank fields, omitting path compression.
INITIALIZE a snapshot stack to hold saved states for rollback.
IMPLEMENT make_set operation to create a singleton set for a given element.
IMPLEMENT find operation to traverse parent pointers to the root without applying path compression.
IMPLEMENT union operation to merge sets using union‑by‑rank, updating parent pointers and ranks accordingly.
IMPLEMENT save operation to push a copy of the current state onto the snapshot stack.
IMPLEMENT restore operation to pop the latest saved state from the snapshot stack and replace the current state.
CREATE tests for basic union‑find functionality:
    VERIFY that make_set creates distinct singletons.
    VERIFY that find returns the correct representative.
    VERIFY that union merges sets according to rank.
CREATE tests for rollback functionality:
    PERFORM unions, SAVE state, PERFORM additional unions, RESTORE state, VERIFY that structure matches the saved snapshot.
CREATE tests for nested save/restore sequences:
    PERFORM a sequence of saves and restores in nested order, VERIFY that each restore returns the structure to the corresponding saved state.
RUN all tests and VERIFY that they all succeed.
