# Correct with a different interface: BlockPool(block_size=..., count=...), block
# indices instead of byte offsets, a memoryview over the arena, and the
# allocation bit kept in each block's last byte.
class PoolExhaustedError(RuntimeError):
    pass


class BlockPool:
    def __init__(self, block_size, count):
        self.bs, self.count = block_size, count
        self.arena = memoryview(bytearray(block_size * count))
        for i in range(count):
            self._set_next(i, i + 1 if i + 1 < count else -1)
        self.free_head = 0 if count else -1

    def _set_next(self, i, nxt):
        self.arena[i * self.bs:i * self.bs + 2] = (nxt & 0xFFFF).to_bytes(2, "little")

    def _next(self, i):
        v = int.from_bytes(self.arena[i * self.bs:i * self.bs + 2], "little")
        return -1 if v == 0xFFFF else v

    def allocate(self):
        if self.free_head == -1:
            raise PoolExhaustedError("pool exhausted")
        i = self.free_head
        self.free_head = self._next(i)
        self.arena[(i + 1) * self.bs - 1] = 1
        return i

    def free(self, index):
        if self.arena[(index + 1) * self.bs - 1] != 1:
            raise RuntimeError("double free")
        self.arena[(index + 1) * self.bs - 1] = 0
        self._set_next(index, self.free_head)
        self.free_head = index
