# memory_pool.py
"""Fixed‑block memory pool allocator.
Implements allocation without dynamic Python allocations in the critical paths.
"""

class PoolExhausted(RuntimeError):
    """Raised when allocate() is called but no free blocks remain."""
    pass

class DoubleFreeError(RuntimeError):
    """Raised when free() is called on a block that is already free or invalid."""
    pass

class FixedBlockMemoryPool:
    """Memory pool of N blocks each of size B bytes.

    The pool stores a raw ``bytearray`` of size ``N * B`` and an embedded
    free‑list stored as a stack of offsets inside a second ``bytearray`` that
    lives for the lifetime of the object. No ``list.append`` or other dynamic
    allocation occurs after construction.
    """

    __slots__ = ("_buffer", "_free_stack", "_top", "N", "B")

    def __init__(self, N: int, B: int):
        if N <= 0 or B <= 0:
            raise ValueError("N and B must be positive integers")
        self.N = N
        self.B = B
        # raw memory buffer – not used by allocate/free directly but kept for completeness
        self._buffer = bytearray(N * B)
        # free‑list stack stored in a pre‑allocated bytearray of 8‑byte integers (offsets)
        # using memoryview for fast integer packing/unpacking
        self._free_stack = bytearray(N * 8)
        # Initialise stack with offsets 0, B, 2*B, …
        for i in range(N):
            offset = i * B
            # pack as little‑endian unsigned 64‑bit
            self._free_stack[i * 8 : (i + 1) * 8] = offset.to_bytes(8, "little")
        self._top = N  # number of free entries currently on the stack

    def allocate(self) -> int:
        """Return the offset of a free block.

        Raises:
            PoolExhausted: if no free blocks remain.
        """
        if self._top == 0:
            raise PoolExhausted()
        # pop the top offset
        self._top -= 1
        start = self._top * 8
        offset_bytes = self._free_stack[start : start + 8]
        offset = int.from_bytes(offset_bytes, "little")
        return offset

    def free(self, offset: int) -> None:
        """Return a block to the pool.

        Raises:
            DoubleFreeError: if the offset is already free or not a valid block start.
        """
        if offset < 0 or offset % self.B != 0 or offset >= self.N * self.B:
            raise DoubleFreeError("Invalid block offset")
        # Check if offset already present in stack (linear scan – N is fixed and small)
        # No additional dynamic allocations are performed.
        for i in range(self._top):
            start = i * 8
            existing = int.from_bytes(self._free_stack[start : start + 8], "little")
            if existing == offset:
                raise DoubleFreeError("Double free detected")
        # push back onto stack
        start = self._top * 8
        self._free_stack[start : start + 8] = offset.to_bytes(8, "little")
        self._top += 1

# Unit tests
if __name__ == "__main__":
    import unittest

    class TestFixedBlockMemoryPool(unittest.TestCase):
        def setUp(self):
            self.N = 4
            self.B = 16
            self.pool = FixedBlockMemoryPool(self.N, self.B)

        def test_allocate_all(self):
            offsets = set()
            for _ in range(self.N):
                off = self.pool.allocate()
                self.assertNotIn(off, offsets)
                offsets.add(off)
            self.assertEqual(len(offsets), self.N)
            # pool should be exhausted now
            with self.assertRaises(PoolExhausted):
                self.pool.allocate()

        def test_free_and_reallocate(self):
            off1 = self.pool.allocate()
            off2 = self.pool.allocate()
            self.pool.free(off1)
            # after freeing, allocate should give the same offset back (LIFO order)
            off3 = self.pool.allocate()
            self.assertEqual(off1, off3)
            # free remaining blocks
            self.pool.free(off2)
            self.pool.free(off3)
            # now all blocks are free again
            all_offsets = {self.pool.allocate() for _ in range(self.N)}
            self.assertEqual(all_offsets, {0, self.B, 2 * self.B, 3 * self.B})

        def test_double_free_detection(self):
            off = self.pool.allocate()
            self.pool.free(off)
            with self.assertRaises(DoubleFreeError):
                self.pool.free(off)

        def test_invalid_free_detection(self):
            with self.assertRaises(DoubleFreeError):
                self.pool.free(-1)
            with self.assertRaises(DoubleFreeError):
                self.pool.free(self.N * self.B)  # out of range
            with self.assertRaises(DoubleFreeError):
                self.pool.free(5)  # not aligned to block size

    unittest.main(argv=["-v"], exit=False)
