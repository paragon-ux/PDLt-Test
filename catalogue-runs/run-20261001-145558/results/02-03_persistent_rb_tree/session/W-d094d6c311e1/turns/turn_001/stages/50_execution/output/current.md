class Node:
    __slots__ = ('key', 'color', 'left', 'right')
    def __init__(self, key, color='red', left=None, right=None):
        self.key = key
        self.color = color
        self.left = left
        self.right = right

def is_red(node):
    return node is not None and node.color == 'red'

def rotate_left(h):
    x = h.right
    h = Node(h.key, h.color, h.left, x.left)
    x = Node(x.key, h.color, h, x.right)
    return x

def rotate_right(h):
    x = h.left
    h = Node(h.key, h.color, x.right, h.right)
    x = Node(x.key, h.color, x.left, h)
    return x

def flip_colors(h):
    h = Node(h.key, 'red' if h.color == 'black' else 'black', h.left, h.right)
    if h.left:
        h.left = Node(h.left.key, 'black' if h.left.color == 'red' else 'red', h.left.left, h.left.right)
    if h.right:
        h.right = Node(h.right.key, 'black' if h.right.color == 'red' else 'red', h.right.left, h.right.right)
    return h

def insert(tree, key):
    def _insert(node):
        if node is None:
            return Node(key)
        if key < node.key:
            left = _insert(node.left)
            node = Node(node.key, node.color, left, node.right)
        elif key > node.key:
            right = _insert(node.right)
            node = Node(node.key, node.color, node.left, right)
        else:
            return node
        if is_red(node.right) and not is_red(node.left):
            node = rotate_left(node)
        if is_red(node.left) and is_red(node.left.left):
            node = rotate_right(node)
        if is_red(node.left) and is_red(node.right):
            node = flip_colors(node)
        return node
    new_root = _insert(tree)
    if new_root.color != 'black':
        new_root = Node(new_root.key, 'black', new_root.left, new_root.right)
    return new_root

def lookup(tree, key):
    node = tree
    while node is not None:
        if key < node.key:
            node = node.left
        elif key > node.key:
            node = node.right
        else:
            return True
    return False

def to_sorted_list(tree):\n    def inorder(node):
        if node is None:
            return []
        return inorder(node.left) + [node.key] + inorder(node.right)
    return inorder(tree)

# Unit tests
if __name__ == '__main__':
    import unittest
    class TestPersistentRBTree(unittest.TestCase):
        def test_persistence(self):
            t1 = None
            t2 = insert(t1, 5)
            t3 = insert(t2, 3)
            t4 = insert(t3, 7)
            self.assertTrue(lookup(t4, 5))
            self.assertTrue(lookup(t4, 3))
            self.assertTrue(lookup(t4, 7))
            self.assertFalse(lookup(t1, 5))
            self.assertFalse(lookup(t2, 3))
            self.assertFalse(lookup(t3, 7))
        def test_sorted_output(self):
            keys = [10, 5, 15, 3, 7]
            tree = None
            for k in keys:
                tree = insert(tree, k)
            self.assertEqual(to_sorted_list(tree), sorted(keys))
        def test_red_black_invariants(self):
            # Simple checks: root black, no red-red, equal black height
            def check(node):
                if node is None:
                    return 1
                if is_red(node):
                    self.assertFalse(is_red(node.left))
                    self.assertFalse(is_red(node.right))
                left_black = check(node.left)
                right_black = check(node.right)
                self.assertEqual(left_black, right_black)
                return left_black + (1 if node.color == 'black' else 0)
            tree = None
            for i in range(1, 20):
                tree = insert(tree, i)
            self.assertEqual(tree.color, 'black')
            check(tree)
    unittest.main()
