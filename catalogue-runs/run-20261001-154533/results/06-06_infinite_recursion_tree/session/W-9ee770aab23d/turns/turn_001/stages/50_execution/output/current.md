class Node:
    def __init__(self, val, children=None):
        self.val = val
        self.children = children or []

def serialize_iterative(root):
    """Iteratively serialize a node tree.
    Returns a string of the form "val(child1,child2,...)".
    Uses an explicit stack to avoid recursion.
    """
    if root is None:
        return "null"
    # Stack holds tuples: (node, state, child_results)
    # state 0 = first visit, 1 = processing children done
    stack = [(root, 0, [])]
    result = None
    while stack:
        node, state, child_res = stack.pop()
        if state == 0:
            # Push a marker to process after children
            stack.append((node, 1, child_res))
            # Push children in reverse order to preserve order
            for child in reversed(node.children):
                stack.append((child, 0, []))
        else:
            # All children have been processed; their results are in child_res
            # Gather child strings from the stack's already built results
            # Since children were processed before the marker, their results are
            # stored in a temporary list attached to the node's entry.
            # Retrieve them from a separate results dict.
            # For simplicity, we collect child strings as we unwind.
            # The child results are accumulated in the markers already.
            # Build the string for this node.
            child_str = ",".join(child_res)
            node_str = f"{node.val}({child_str})" if child_str else f"{node.val}()"
            if stack:
                # Append this result to the parent's child_res list
                parent_node, parent_state, parent_child_res = stack[-1]
                parent_child_res.append(node_str)
            else:
                result = node_str
    return result

# Verification test script
if __name__ == "__main__":
    # Build a linear chain of depth 50000
    depth = 50000
    root = Node(1)
    current = root
    for i in range(2, depth + 1):
        child = Node(i)
        current.children.append(child)
        current = child
    # Serialize using iterative function
    output = serialize_iterative(root)
    # Simple sanity check: output should start with "1(2(3(" and end with many closing parentheses
    assert output.startswith("1(2(3"), "Serialization output format incorrect"
    # Ensure the length matches expectation roughly (each node adds digits and parentheses)
    expected_min_len = depth * 2  # very rough lower bound
    assert len(output) > expected_min_len, "Output length unexpectedly short"
    print("Serialization completed successfully for depth", depth)
