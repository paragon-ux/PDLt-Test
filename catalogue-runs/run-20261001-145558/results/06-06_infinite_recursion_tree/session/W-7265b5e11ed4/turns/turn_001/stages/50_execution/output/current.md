class Node:
    def __init__(self, val, children=None):
        self.val = val
        self.children = children or []

def serialize_iterative(root):
    """Serialize a tree to a string using an explicit stack to avoid recursion.
    The format matches the original recursive implementation: "val(child1,child2,...)".
    """
    if root is None:
        return "null"
    # Stack holds tuples: (node, iterator over its children, already_serialized_children list)
    stack = []
    result_parts = []
    stack.append((root, iter(root.children), []))
    while stack:
        node, children_iter, child_strs = stack[-1]
        try:
            child = next(children_iter)
            # Push child onto stack to process it before continuing with current node
            stack.append((child, iter(child.children), []))
        except StopIteration:
            # All children processed, build this node's string
            serialized_children = ",".join(child_strs)
            node_str = f"{node.val}({serialized_children})"
            stack.pop()
            if stack:
                # Append this node's string to its parent's child list
                stack[-1][2].append(node_str)
            else:
                # This is the root node
                result_parts.append(node_str)
    return result_parts[0]

# Test on a deep chain of depth 50000
root = Node(1)
current = root
for i in range(2, 50001):
    child = Node(i)
    current.children.append(child)
    current = child

# Serialize without recursion error
serialized = serialize_iterative(root)
print('Length of serialization:', len(serialized))
print('First 50 chars:', serialized[:50])
print('Last 50 chars:', serialized[-50:])
