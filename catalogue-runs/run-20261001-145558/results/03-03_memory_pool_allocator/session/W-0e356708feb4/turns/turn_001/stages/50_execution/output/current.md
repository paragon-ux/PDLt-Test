"""Fixed‑block memory pool allocator.

Provides a simple allocator that manages a pre‑allocated bytearray divided into N fixed‑size blocks.
It uses an embedded free‑list stored inside the buffer (each free block holds the index of the next free block).
"""

class PoolExhausted(RuntimeError):
    """Raised when allocate() is called but no free blocks remain."""
    pass

class DoubleFreeError(RuntimeError):
    """Raised when free() is called on an offset that is already free."""
    pass

class FixedBlockMemoryPool:
    """Memory pool of N blocks, each B bytes.

    The underlying storage is a ``bytearray`` of size ``N * B``. The free list is embedded in the first 4 bytes of each block
    (as a little‑endian unsigned 32‑bit integer) and stores the index of the next free block. ``-1`` (0xFFFFFFFF) marks the end of the list.
    """

    _END = 0xFFFFFFFF

    def __init__(self, num_blocks: int, block_size: int):
        if num_blocks <= 0:
            raise ValueError("num_blocks must be positive")
        if block_size <= 0:
            raise ValueError("block_size must be positive")
        self.num_blocks = num_blocks
        self.block_size = block_size
        self.buffer = bytearray(num_blocks * block_size)
        # initialise free list
        for i in range(num_blocks):
            next_idx = i + 1 if i + 1 < num_blocks else self._END
            self._write_next(i, next_idx)
        self.free_head = 0  # index of first free block
        self._allocated = set()  # track allocated offsets for double‑free detection

    def _block_offset(self, index: int) -> int:
        return index * self.block_size

    def _write_next(self, index: int, next_idx: int) -> None:
        offset = self._block_offset(index)
        self.buffer[offset:offset+4] = next_idx.to_bytes(4, "little")

    def _read_next(self, index: int) -> int:
        offset = self._block_offset(index)
        return int.from_bytes(self.buffer[offset:offset+4], "little")

    def allocate(self) -> int:
        """Return the offset of a free block.

        Raises:
            PoolExhausted: if no free block is available.
        """
        if self.free_head == self._END:
            raise PoolExhausted("Memory pool exhausted")
        alloc_index = self.free_head
        self.free_head = self._read_next(alloc_index)
        self._allocated.add(self._block_offset(alloc_index))
        return self._block_offset(alloc_index)

    def free(self, offset: int) -> None:
        """Return a block to the pool.

        Args:
            offset: The integer offset previously returned by ``allocate``.

        Raises:
            ValueError: If ``offset`` is not on a block boundary or out of range.
            DoubleFreeError: If the block is already free.
        """
        if offset % self.block_size != 0:
            raise ValueError("Offset does not align with block size")
        index = offset // self.block_size
        if index < 0 or index >= self.num_blocks:
            raise ValueError("Offset out of pool range")
        if offset not in self._allocated:
            raise DoubleFreeError("Block at offset {} already free".format(offset))
        # prepend this block to the free list
        self._write_next(index, self.free_head)
        self.free_head = index
        self._allocated.remove(offset)

# ---------------------- Tests ----------------------
import unittest

class TestFixedBlockMemoryPool(unittest.TestCase):
    def setUp(self):
        self.N = 8
        self.B = 16
        self.pool = FixedBlockMemoryPool(self.N, self.B)

    def test_allocate_all_blocks(self):
        offsets = [self.pool.allocate() for _ in range(self.N)]
        # offsets should be distinct and correctly spaced
        self.assertEqual(len(set(offsets)), self.N)
        for i, off in enumerate(offsets):
            self.assertEqual(off, i * self.B)
        # further allocation must raise
        with self.assertRaises(PoolExhausted):
            self.pool.allocate()

    def test_free_and_reallocate(self):
        offsets = [self.pool.allocate() for _ in range(self.N)]
        # free every even index
        for off in offsets[::2]:
            self.pool.free(off)
        # allocate again should succeed for half the blocks
        reallocated = [self.pool.allocate() for _ in range(self.N // 2)]
        self.assertEqual(len(set(reallocated)), self.N // 2)
        # after reallocation pool is exhausted again
        with self.assertRaises(PoolExhausted):
            self.pool.allocate()
        # free remaining blocks then allocate all
        for off in offsets[1::2]:
            self.pool.free(off)
        for off in reallocated:
            self.pool.free(off)
        all_offsets = [self.pool.allocate() for _ in range(self.N)]
        self.assertEqual(len(set(all_offsets)), self.N)

    def test_double_free_detection(self):
        off = self.pool.allocate()
        self.pool.free(off)
        with self.assertRaises(DoubleFreeError):
            self.pool.free(off)
        # also double free of never‑allocated offset
        with self.assertRaises(DoubleFreeError):
            self.pool.free(0)

    def test_invalid_free(self):
        # offset not aligned
        with self.assertRaises(ValueError):
            self.pool.free(1)
        # offset out of range
        with self.assertRaises(ValueError):
            self.pool.free(self.N * self.B)

if __name__ == "__main__":
    unittest.main()
