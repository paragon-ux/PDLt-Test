```python
class Node:
    def __init__(self, val, children=None):
        self.val = val
        self.children = children or []

def serialize_iterative(root):
    """Iteratively serialize a tree to the same format as the recursive version.
    The format is: val(child1,child2,...) where children are serialized
    recursively. For a chain (single child) this becomes a nested string.
    """
    if root is None:
        return "null"
    # Use a stack to perform a depth‑first traversal. Each stack entry holds
    # (node, state, child_index). State 0 means we have not processed the node
    # yet; state 1 means we have processed its children and are ready to emit
    # the closing parenthesis.
    stack = [(root, 0, 0)]
    # Result fragments will be built in a list for efficiency.
    parts = []
    while stack:
        node, state, idx = stack.pop()
        if state == 0:
            # Emit the node's value and opening parenthesis.
            parts.append(str(node.val))
            parts.append('(')
            # After children are processed we need to close the parenthesis.
            stack.append((node, 1, 0))
            # Push children in reverse order so that the leftmost child is
            # processed first (stack is LIFO).
            for child in reversed(node.children):
                stack.append((child, 0, 0))
        else:
            # All children have been serialized; close this node.
            parts.append(')')
    # The algorithm adds an extra pair of parentheses around the root.
    # Remove the outermost parentheses to match the recursive output.
    # The first character is the root value, then '(' ... ')' for its children.
    # The final list ends with a ')' for the root, which we keep.
    serialized = ''.join(parts)
    # The recursive version does not add a trailing parenthesis for the root
    # when there are no children; however our algorithm always adds one. To
    # emulate the exact format, we need to collapse consecutive empty
    # parentheses "()" that represent leaf nodes without children.
    # The recursive version prints "val()" for leaf nodes, so the representation
    # is already correct.
    return serialized

# Test code constructing a deep chain of 50,000 nodes.
if __name__ == "__main__":
    depth = 50000
    root = Node(1)
    current = root
    for i in range(2, depth + 1):
        child = Node(i)
        current.children.append(child)
        current = child
    # Serialize using the iterative function.
    result = serialize_iterative(root)
    # Print a short prefix to verify output shape without overwhelming stdout.
    print(result[:100])
    # Verify that the result length matches expectation (approximate).
    expected_len = sum(len(str(i)) + 2 for i in range(1, depth + 1))
    assert len(result) == expected_len, "Serialization length mismatch"
    print("Serialization completed without stack overflow.")
```
