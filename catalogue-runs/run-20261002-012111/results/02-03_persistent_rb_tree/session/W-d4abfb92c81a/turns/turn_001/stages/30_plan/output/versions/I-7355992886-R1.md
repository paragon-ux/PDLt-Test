DEFINE node data class with attributes key, color, left, right.
DEFINE tree data class with attribute root.
IMPLEMENT insert(tree, key) RETURNING new_tree using path copying and red-black fix-up.
IMPLEMENT lookup(tree, key) RETURNING bool via binary search.
IMPLEMENT to_sorted_list(tree) RETURNING list via in-order traversal.
IMPLEMENT rotate_left(node) and rotate_right(node) as helpers.
IMPLEMENT recolor(node) and fix_insert(node) as red-black fix-up.
IMPLEMENT verify_red_black_invariants(tree) that checks root black, no red-red parent-child, equal black-height.
IMPLEMENT verify_bst_ordering(tree) that checks in-order traversal yields sorted keys.
IMPLEMENT test_persistence:
    CREATE baseline_tree as empty tree.
    PERFORM insert(baseline_tree, key) => new_tree.
    ASSERT baseline_tree unchanged.
    CALL verify_red_black_invariants(new_tree).
    CALL verify_bst_ordering(new_tree).
IMPLEMENT test_multiple_insertions:
    SET current_tree to empty tree.
    FOR each key in a sample key set:
        PERFORM insert(current_tree, key) => next_tree.
        ASSERT current_tree unchanged.
        CALL verify_red_black_invariants(next_tree).
        CALL verify_bst_ordering(next_tree).
        UPDATE current_tree to next_tree.
RUN all test cases and report results.
