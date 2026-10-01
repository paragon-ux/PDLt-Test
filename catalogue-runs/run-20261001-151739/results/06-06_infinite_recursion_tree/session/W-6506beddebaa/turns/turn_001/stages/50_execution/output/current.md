```python
class Node:
    def __init__(self, val, children=None):
        self.val = val
        self.children = children or []

def serialize_iterative(root):
    """Iteratively serialize a tree of Node objects.
    Returns a string representation of the form "val(child1,child2,...)".
    Handles very deep trees without recursion depth limits.
    """
    if root is None:
        return "null"
    # Stack holds tuples: (node, state, children_serialized)
    # state 0 = first visit, need to process children
    # state 1 = children processed, assemble string
    stack = [(root, 0, [])]
    while stack:
        node, state, child_strs = stack.pop()
        if state == 0:
            # Push a frame to handle this node after its children
            stack.append((node, 1, []))
            # Push child frames in reverse order to preserve left-to-right order
            for child in reversed(node.children):
                stack.append((child, 0, []))
        else:
            # All children are serialized; child_strs are collected from stack
            # The child results are stored in the previous frames' child_strs list
            # Retrieve serialized strings of children from the stack's stored data
            # They were appended to the parent frame's child_strs when each child finished
            # We'll reconstruct by gathering from a temporary list built during unwinding
            # Since we cannot directly pass data, we use a sentinel technique:
            # The parent frame's child_strs list was empty; we fill it now.
            # The children results are already placed on the stack as strings.
            # To simplify, we store intermediate results on a separate list.
            # We'll use a dict to map node id to its serialized string.
            # However, to keep it pure iterative without extra structures, we can
            # push the serialized string back onto the stack as a special marker.
            # For clarity, we adopt a helper list.
            pass
    # The above approach is complex; a clearer implementation uses an explicit
    # stack of (node, iterator) and builds the string progressively.
    # Re-implement below:

def serialize_iterative(root):
    if root is None:
        return "null"
    result_parts = []
    stack = [(root, 0)]  # (node, child_index)
    while stack:
        node, idx = stack[-1]
        if idx == 0:
            # Enter node: write its value and '('
            result_parts.append(str(node.val))
            result_parts.append('(')
        if idx < len(node.children):
            # Process next child
            stack[-1] = (node, idx + 1)
            # Add comma if not first child
            if idx > 0:
                result_parts.append(',')
            stack.append((node.children[idx], 0))
        else:
            # All children processed, close ')'
            result_parts.append(')')
            stack.pop()
    return ''.join(result_parts)

# Test on a chain of 50,000 nodes
root = Node(1)
current = root
for i in range(2, 50001):
    child = Node(i)
    current.children.append(child)
    current = child

# Serialize
serialized = serialize_iterative(root)
print('Serialized length:', len(serialized))
print('First 100 chars:', serialized[:100])
```
