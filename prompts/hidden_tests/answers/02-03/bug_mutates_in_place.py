# Wrong: insert mutates the existing tree (no path copying), so old versions change.
class Node:
    def __init__(self, key):
        self.key, self.left, self.right, self.red = key, None, None, True


def insert(tree, key):
    if tree is None:
        return Node(key)
    node = tree
    while True:
        if key < node.key:
            if node.left is None:
                node.left = Node(key)
                break
            node = node.left
        elif key > node.key:
            if node.right is None:
                node.right = Node(key)
                break
            node = node.right
        else:
            break
    return tree


def lookup(tree, key):
    while tree is not None:
        if key == tree.key:
            return True
        tree = tree.left if key < tree.key else tree.right
    return False


def to_sorted_list(tree):
    out, stack, node = [], [], tree
    while stack or node is not None:
        while node is not None:
            stack.append(node)
            node = node.left
        node = stack.pop()
        out.append(node.key)
        node = node.right
    return out
