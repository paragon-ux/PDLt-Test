class PoolExhausted(Exception):
    """Exception raised when the memory pool is exhausted."""
    pass


class FixedBlockMemoryPool:
    """Fixed-size block memory pool.

    The pool consists of a contiguous bytearray of size N * B where N is the
    number of blocks and B is the block size. A free list is stored inside the
    buffer itself using 4‑byte integer offsets (little‑endian). The first 4
    bytes of each free block hold the offset of the next free block; the last
    free block stores -1.
    """

    def __init__(self, N: int, B: int):
        if N <= 0:
            raise ValueError("N must be positive")
        if B <= 4:
            raise ValueError("B must be larger than pointer size (4)")
        self.N = N
        self.B = B
        self.buffer = bytearray(N * B)
        # Initialise free list: each block's first 4 bytes store the offset
        # of the next free block.
        for i in range(N):
            next_offset = (i + 1) * B if i + 1 < N else -1
            self._write_int(i * B, next_offset)
        self.free_head = 0  # offset of first free block
        self._allocated = set()  # track allocated offsets for double‑free detection

    def _write_int(self, offset: int, value: int) -> None:
        # Store a signed 32‑bit integer at the given offset.
        self.buffer[offset:offset+4] = value.to_bytes(4, byteorder="little", signed=True)

    def _read_int(self, offset: int) -> int:
        return int.from_bytes(self.buffer[offset:offset+4], byteorder="little", signed=True)

    def allocate(self) -> int:
        """Allocate a block and return its offset.

        Raises:
            PoolExhausted: if no free blocks are available.
        """
        if self.free_head == -1:
            raise PoolExhausted("No free blocks available")
        allocated_offset = self.free_head
        # The next free block is stored in the first 4 bytes of the current block.
        self.free_head = self._read_int(allocated_offset)
        # Mark block as allocated.
        self._allocated.add(allocated_offset)
        return allocated_offset

    def free(self, offset: int) -> None:
        """Return a block to the pool.

        Args:
            offset: The offset previously returned by allocate().

        Raises:
            ValueError: if the offset is invalid or the block is already free.
        """
        if offset % self.B != 0 or not (0 <= offset < self.N * self.B):
            raise ValueError("Offset does not correspond to a block in the pool")
        if offset not in self._allocated:
            raise ValueError("Double free detected or block was never allocated")
        # Insert the freed block at the head of the free list.
        self._write_int(offset, self.free_head)
        self.free_head = offset
        self._allocated.remove(offset)

# Test suite
if __name__ == "__main__":
    import unittest

    class TestFixedBlockMemoryPool(unittest.TestCase):
        def setUp(self):
            self.N = 8
            self.B = 16
            self.pool = FixedBlockMemoryPool(self.N, self.B)

        def test_allocate_all_blocks(self):
            offsets = set()
            for _ in range(self.N):
                off = self.pool.allocate()
                self.assertNotIn(off, offsets)
                offsets.add(off)
            self.assertEqual(len(offsets), self.N)
            # Next allocation should raise PoolExhausted
            with self.assertRaises(PoolExhausted):
                self.pool.allocate()

        def test_free_and_reallocate(self):
            offs = [self.pool.allocate() for _ in range(self.N)]
            # Free half of them
            for off in offs[:self.N // 2]:
                self.pool.free(off)
            # Reallocate the same number of blocks
            reallocated = set()
            for _ in range(self.N // 2):
                off = self.pool.allocate()
                self.assertNotIn(off, reallocated)
                reallocated.add(off)
            # Ensure no PoolExhausted raised
            # All remaining blocks should still be allocated
            with self.assertRaises(PoolExhausted):
                self.pool.allocate()

        def test_double_free_detection(self):
            off = self.pool.allocate()
            self.pool.free(off)
            with self.assertRaises(ValueError):
                self.pool.free(off)

        def test_invalid_offset(self):
            with self.assertRaises(ValueError):
                self.pool.free(-4)
            with self.assertRaises(ValueError):
                self.pool.free(self.N * self.B)  # beyond buffer
            with self.assertRaises(ValueError):
                self.pool.free(3)  # not aligned to block size

    unittest.main(argv=["-v"], exit=False)
