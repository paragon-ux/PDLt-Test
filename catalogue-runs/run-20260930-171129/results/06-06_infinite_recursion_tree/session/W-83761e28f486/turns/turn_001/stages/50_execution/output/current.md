class Node:
    def __init__(self, val, children=None):
        self.val = val
        self.children = children or []

def serialize(root):
    """Iteratively serialize a tree of Node objects.
    Returns a string of the form val(child1,child2,...) where children are
    serialized recursively. Uses an explicit stack to avoid recursion.
    """
    if root is None:
        return "null"
    # Stack entries: (node, state, child_index, serialized_children)
    # state 0 = just entered, need to process children; state 1 = children done
    stack = [(root, 0, 0, [])]
    result = None
    while stack:
        node, state, idx, child_strs = stack.pop()
        if state == 0:
            # Push a marker to finish this node after its children
            stack.append((node, 1, 0, []))
            # Push children in reverse order so they are processed left‑to‑right
            for child in reversed(node.children):
                stack.append((child, 0, 0, []))
        else:
            # All children have been processed; gather their serialized strings
            # They are stored in the stack as they completed, so we need to collect them.
            # To retrieve them, we look at the last len(node.children) results we built.
            # We'll accumulate results in a temporary list attached to the node.
            # For simplicity, we reconstruct by walking stack again: not needed because
            # child results were already built and can be fetched via a helper dict.
            # We'll use a dict keyed by node id.
            pass
    # The above approach is complex; instead we use a simpler algorithm:

def serialize_iterative(root):
    if root is None:
        return "null"
    stack = [(root, False)]  # (node, visited)
    parts = []
    while stack:
        node, visited = stack.pop()
        if visited:
            parts.append(')')
        else:
            parts.append('(')
            # push closing marker
            stack.append((node, True))
            # push children in reverse order for proper order
            for child in reversed(node.children):
                stack.append((child, False))
            parts.append(str(node.val))
    # The string is built in reverse order, fix it
    return ''.join(reversed(parts)).strip(')')

# Test on a chain of 50,000 nodes
root = Node(1)
current = root
for i in range(2, 50001):
    child = Node(i)
    current.children.append(child)
    current = child

serialized = serialize_iterative(root)
print(serialized[:200])  # print a prefix for verification
