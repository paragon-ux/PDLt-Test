# Wrong: double free corrupts the free list instead of being detected.
import struct


class PoolExhausted(Exception):
    pass


class MemoryPool:
    def __init__(self, num_blocks, block_size):
        self.block_size = block_size
        self.buffer = bytearray(num_blocks * block_size)
        for i in range(num_blocks):
            struct.pack_into("<i", self.buffer, i * block_size, (i + 1) * block_size if i + 1 < num_blocks else -1)
        self.head = 0 if num_blocks else -1

    def allocate(self):
        if self.head == -1:
            raise PoolExhausted()
        offset = self.head
        self.head = struct.unpack_from("<i", self.buffer, offset)[0]
        return offset

    def free(self, offset):
        struct.pack_into("<i", self.buffer, offset, self.head)
        self.head = offset
