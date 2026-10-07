# Correct with a different interface: the recursive original is kept, and the
# iterative version builds each node's string bottom-up from a post-order list.
class Node:
    def __init__(self, val, children=None):
        self.val = val
        self.children = children or []


def serialize(node):
    if node is None:
        return "null"
    child_strs = ",".join(serialize(c) for c in node.children)
    return f"{node.val}({child_strs})"


def serialize_iterative(root):
    if root is None:
        return "null"
    order, stack = [], [root]
    while stack:
        n = stack.pop()
        order.append(n)
        stack.extend(n.children)
    text = {}
    for n in reversed(order):
        text[id(n)] = f"{n.val}(" + ",".join(text.pop(id(c)) for c in n.children) + ")"
    return text[id(root)]
