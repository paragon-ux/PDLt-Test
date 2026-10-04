# Wrong: keeps the free list in a Python list with no backing buffer, and
# signals exhaustion with IndexError.
class Pool:
    def __init__(self, n, block_size):
        self.free_blocks = [i * block_size for i in range(n)][::-1]
        self.used = set()

    def allocate(self):
        offset = self.free_blocks.pop()
        self.used.add(offset)
        return offset

    def free(self, offset):
        if offset not in self.used:
            raise ValueError("double free")
        self.used.remove(offset)
        self.free_blocks.append(offset)
