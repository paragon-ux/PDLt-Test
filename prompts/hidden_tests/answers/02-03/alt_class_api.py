# Correct with a different interface: an immutable tree object whose methods return
# new trees; the empty tree is the class's default instance.
class PersistentRBTree:
    __slots__ = ("root",)

    def __init__(self, root=None):
        self.root = root

    @staticmethod
    def _red(n):
        return n is not None and n[0] == "R"

    @classmethod
    def _bal(cls, c, l, k, r):
        R = cls._red
        if c == "B":
            if R(l) and R(l[1]):
                return ("R", ("B",) + l[1][1:], l[2], ("B", l[3], k, r))
            if R(l) and R(l[3]):
                return ("R", ("B", l[1], l[2], l[3][1]), l[3][2], ("B", l[3][3], k, r))
            if R(r) and R(r[1]):
                return ("R", ("B", l, k, r[1][1]), r[1][2], ("B", r[1][3], r[2], r[3]))
            if R(r) and R(r[3]):
                return ("R", ("B", l, k, r[1]), r[2], ("B",) + r[3][1:])
        return (c, l, k, r)

    @classmethod
    def _ins(cls, n, key):
        if n is None:
            return ("R", None, key, None)
        c, l, k, r = n
        if key < k:
            return cls._bal(c, cls._ins(l, key), k, r)
        if key > k:
            return cls._bal(c, l, k, cls._ins(r, key))
        return n

    def insert(self, key):
        c, l, k, r = self._ins(self.root, key)
        return PersistentRBTree(("B", l, k, r))

    def lookup(self, key):
        n = self.root
        while n is not None:
            if key == n[2]:
                return True
            n = n[1] if key < n[2] else n[3]
        return False

    def to_sorted_list(self):
        out, stack, n = [], [], self.root
        while stack or n is not None:
            while n is not None:
                stack.append(n)
                n = n[1]
            n = stack.pop()
            out.append(n[2])
            n = n[3]
        return out
