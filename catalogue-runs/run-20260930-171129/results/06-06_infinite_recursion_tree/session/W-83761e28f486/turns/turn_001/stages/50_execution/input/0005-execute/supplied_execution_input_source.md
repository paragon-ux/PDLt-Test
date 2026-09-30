The following tree serialization function blows the stack on deep trees. Diagnose why and convert it to an iterative solution that handles trees of depth 100,000+.

```python
class Node:
    def __init__(self, val, children=None):
        self.val = val
        self.children = children or []

def serialize(node):
    if node is None:
        return "null"
    child_strs = ",".join(serialize(c) for c in node.children)
    return f"{node.val}({child_strs})"

# Build a deep chain: 1 -> 2 -> 3 -> ... -> 50000
root = Node(1)
current = root
for i in range(2, 50001):
    child = Node(i)
    current.children.append(child)
    current = child

print(serialize(root)[:100])  # RecursionError!
```

Provide the iterative solution and test it on a depth-50000 chain.
