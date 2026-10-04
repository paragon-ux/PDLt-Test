"""Okasaki-style persistent red-black tree (path copying via immutable tuples)."""
from collections import namedtuple

RED, BLACK = "R", "B"
Node = namedtuple("Node", "color left key right")


def _balance(color, left, key, right):
    if color == BLACK:
        if left and left.color == RED and left.left and left.left.color == RED:
            a, x, b, y, c = left.left.left, left.left.key, left.left.right, left.key, left.right
            return Node(RED, Node(BLACK, a, x, b), y, Node(BLACK, c, key, right))
        if left and left.color == RED and left.right and left.right.color == RED:
            a, x, b, y, c = left.left, left.key, left.right.left, left.right.key, left.right.right
            return Node(RED, Node(BLACK, a, x, b), y, Node(BLACK, c, key, right))
        if right and right.color == RED and right.left and right.left.color == RED:
            b, y, c, z, d = right.left.left, right.left.key, right.left.right, right.key, right.right
            return Node(RED, Node(BLACK, left, key, b), y, Node(BLACK, c, z, d))
        if right and right.color == RED and right.right and right.right.color == RED:
            b, y, c, z, d = right.left, right.key, right.right.left, right.right.key, right.right.right
            return Node(RED, Node(BLACK, left, key, b), y, Node(BLACK, c, z, d))
    return Node(color, left, key, right)


def _ins(tree, key):
    if tree is None:
        return Node(RED, None, key, None)
    if key < tree.key:
        return _balance(tree.color, _ins(tree.left, key), tree.key, tree.right)
    if key > tree.key:
        return _balance(tree.color, tree.left, tree.key, _ins(tree.right, key))
    return tree


def insert(tree, key):
    root = _ins(tree, key)
    return Node(BLACK, root.left, root.key, root.right)


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
