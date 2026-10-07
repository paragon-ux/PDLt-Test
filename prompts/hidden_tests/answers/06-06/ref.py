class Node:
    def __init__(self, val, children=None):
        self.val = val
        self.children = children or []


def serialize(node):
    if node is None:
        return "null"
    out = []
    # Each frame: (node, index of the next child to emit).
    stack = [(node, 0)]
    out.append(f"{node.val}(")
    while stack:
        current, i = stack.pop()
        if i < len(current.children):
            if i > 0:
                out.append(",")
            stack.append((current, i + 1))
            child = current.children[i]
            out.append(f"{child.val}(")
            stack.append((child, 0))
        else:
            out.append(")")
    return "".join(out)
