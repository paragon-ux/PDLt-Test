# Wrong: persistent, but never rebalances, so ascending inserts degrade to a
# linked list and the recursive insert exhausts the recursion limit.
def insert(tree, key):
    if tree is None:
        return (None, key, None)
    left, k, right = tree
    if key < k:
        return (insert(left, key), k, right)
    if key > k:
        return (left, k, insert(right, key))
    return tree


def lookup(tree, key):
    while tree is not None:
        if key == tree[1]:
            return True
        tree = tree[0] if key < tree[1] else tree[2]
    return False


def to_sorted_list(tree):
    out, stack, node = [], [], tree
    while stack or node is not None:
        while node is not None:
            stack.append(node)
            node = node[0]
        node = stack.pop()
        out.append(node[1])
        node = node[2]
    return out
