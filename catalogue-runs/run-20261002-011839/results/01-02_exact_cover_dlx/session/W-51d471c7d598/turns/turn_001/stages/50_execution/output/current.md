import itertools

# Define the universe and sets
U = set([1,2,3,4,5,6,7,8,9])
sets = {
    'S1': {1,2,3},
    'S2': {4,5,6},
    'S3': {7,8,9},
    'S4': {1,4,7},
    'S5': {2,5,8},
    'S6': {3,6,9},
    'S7': {1,5,9},
    'S8': {2,6,7},
    'S9': {3,4,8},
}

# Build the exact cover solver using Algorithm X (dancing links not required for this tiny problem)
def exact_covers(universe, collection):
    """Yield all exact covers of `universe` using sets from `collection`.
    Each cover is a list of set identifiers.
    """
    # Convert to list for deterministic ordering
    items = list(universe)
    # Precompute mapping from element to sets containing it
    elem_to_sets = {e: [s for s, elems in collection.items() if e in elems] for e in items}
    # Recursive backtracking
    def backtrack(remaining, chosen):
        if not remaining:
            yield list(chosen)
            return
        # Choose the element with fewest options (heuristic)
        e = min(remaining, key=lambda x: len(elem_to_sets[x]))
        for s in elem_to_sets[e]:
            if collection[s].issubset(remaining):
                new_remaining = remaining - collection[s]
                chosen.append(s)
                yield from backtrack(new_remaining, chosen)
                chosen.pop()
    yield from backtrack(set(universe), [])

# Find and print all exact covers
covers = list(exact_covers(U, sets))
print("Exact covers (list of set identifiers):")
for cover in covers:
    print(cover)

# Self‑contained test verifying each reported solution covers U exactly once
def test_covers():
    assert covers, "No exact covers found"
    for cover in covers:
        covered = set()
        for sid in cover:
            elems = sets[sid]
            # Ensure no overlap
            assert covered.isdisjoint(elems), f"Overlap in cover {cover} for element {covered & elems}"
            covered.update(elems)
        assert covered == U, f"Cover {cover} does not cover all elements"
    print("All reported covers verified successfully.")

if __name__ == "__main__":
    test_covers()
