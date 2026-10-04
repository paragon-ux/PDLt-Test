# Wrong: the recursive original; a deep chain exceeds the recursion limit.
class Node:
    def __init__(self, val, children=None):
        self.val = val
        self.children = children or []


def serialize(node):
    if node is None:
        return "null"
    child_strs = ",".join(serialize(c) for c in node.children)
    return f"{node.val}({child_strs})"
