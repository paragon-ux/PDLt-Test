class PoolExhausted(Exception):
    """Raised when no free blocks are available in the pool."""

class DoubleFreeError(Exception):
    """Raised when an attempt is made to free a block that is already free."""

class FixedBlockPool:
    """Fixed‑size block allocator with an embedded free‑list.

    The pool is backed by a ``bytearray`` of size ``N * B`` where ``N`` is the
    number of blocks and ``B`` the block size in bytes. The first ``B`` bytes of
    each block store the offset of the next free block (as a little‑endian
    unsigned integer). ``allocate`` and ``free`` manipulate only this embedded
    list and never perform dynamic allocation after construction.
    """

    def __init__(self, num_blocks: int, block_size: int):
        if num_blocks <= 0:
            raise ValueError("num_blocks must be positive")
        if block_size <= 0:
            raise ValueError("block_size must be positive")
        self.N = num_blocks
        self.B = block_size
        self.buffer = bytearray(self.N * self.B)
        # Initialize free list: each block points to the next block
        for i in range(self.N):
            next_offset = (i + 1) * self.B if i + 1 < self.N else None
            self._write_next(i * self.B, next_offset)
        self.free_head = 0  # offset of first free block

    def _write_next(self, offset: int, next_offset):
        """Store ``next_offset`` (or ``None``) at ``offset`` within the buffer.

        The offset is stored as an unsigned 8‑byte integer. ``None`` is encoded as
        the sentinel value ``0xFFFFFFFFFFFFFFFF``.
        """
        sentinel = (1 << 64) - 1
        value = sentinel if next_offset is None else next_offset
        self.buffer[offset:offset + 8] = value.to_bytes(8, "little")

    def _read_next(self, offset: int):
        """Read the stored next offset at ``offset``.

        Returns ``None`` if the sentinel value is present.
        """
        sentinel = (1 << 64) - 1
        value = int.from_bytes(self.buffer[offset:offset + 8], "little")
        return None if value == sentinel else value

    def allocate(self) -> int:
        """Return the offset of a free block.

        Raises ``PoolExhausted`` when no blocks remain.
        """
        if self.free_head is None:
            raise PoolExhausted("No free blocks available")
        offset = self.free_head
        # Update head to the next free block stored in the current block
        self.free_head = self._read_next(offset)
        return offset

    def free(self, offset: int) -> None:
        """Return a previously allocated block to the pool.

        ``offset`` must be a valid block start address. Raises ``ValueError`` for
        out‑of‑range or misaligned offsets and ``DoubleFreeError`` if the block is
        already free.
        """
        if not (0 <= offset < self.N * self.B) or (offset % self.B) != 0:
            raise ValueError("Invalid block offset")
        # Detect double free by walking the free list (O(N) but N is typically
        # small for a fixed‑size pool). This satisfies the requirement without
        # extra dynamic structures.
        cur = self.free_head
        while cur is not None:
            if cur == offset:
                raise DoubleFreeError(f"Block at offset {offset} already free")
            cur = self._read_next(cur)
        # Insert this block at the head of the free list
        self._write_next(offset, self.free_head)
        self.free_head = offset

# Test suite
if __name__ == "__main__":
    import unittest

    class TestFixedBlockPool(unittest.TestCase):
        def setUp(self):
            self.N = 8
            self.B = 16
            self.pool = FixedBlockPool(self.N, self.B)

        def test_allocate_all(self):
            offsets = set()
            for _ in range(self.N):
                off = self.pool.allocate()
                self.assertNotIn(off, offsets)
                self.assertTrue(0 <= off < self.N * self.B)
                self.assertEqual(off % self.B, 0)
                offsets.add(off)
            with self.assertRaises(PoolExhausted):
                self.pool.allocate()

        def test_free_and_reallocate(self):
            allocated = [self.pool.allocate() for _ in range(self.N)]
            # Free half of them
            for off in allocated[:4]:
                self.pool.free(off)
            # Reallocate those freed blocks
            reallocated = [self.pool.allocate() for _ in range(4)]
            self.assertCountEqual(allocated[:4], reallocated)
            # Remaining blocks should still be allocated
            with self.assertRaises(PoolExhausted):
                self.pool.allocate()

        def test_double_free_detection(self):
            off = self.pool.allocate()
            self.pool.free(off)
            with self.assertRaises(DoubleFreeError):
                self.pool.free(off)

        def test_invalid_free(self):
            with self.assertRaises(ValueError):
                self.pool.free(-self.B)
            with self.assertRaises(ValueError):
                self.pool.free(self.N * self.B)  # out of range
            with self.assertRaises(ValueError):
                self.pool.free(7)  # misaligned

    unittest.main(argv=["-v"], exit=False)
