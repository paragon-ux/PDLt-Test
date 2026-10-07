import struct


class PoolExhausted(Exception):
    pass


class DoubleFree(Exception):
    pass


_END = 0xFFFFFFFF


class MemoryPool:
    """Each free block's first 4 bytes hold the offset of the next free block."""

    def __init__(self, num_blocks, block_size):
        if block_size < 4:
            raise ValueError("blocks must hold a 4-byte link")
        self.num_blocks, self.block_size = num_blocks, block_size
        self.buffer = bytearray(num_blocks * block_size)
        self.in_use = bytearray(num_blocks)  # one byte per block, for double-free detection
        for i in range(num_blocks):
            nxt = (i + 1) * block_size if i + 1 < num_blocks else _END
            struct.pack_into("<I", self.buffer, i * block_size, nxt)
        self.head = 0 if num_blocks else _END

    def allocate(self):
        if self.head == _END:
            raise PoolExhausted("no free blocks")
        offset = self.head
        self.head = struct.unpack_from("<I", self.buffer, offset)[0]
        self.in_use[offset // self.block_size] = 1
        return offset

    def free(self, offset):
        if offset % self.block_size or not 0 <= offset < len(self.buffer):
            raise ValueError(f"bad offset {offset}")
        if not self.in_use[offset // self.block_size]:
            raise DoubleFree(f"block at {offset} is already free")
        self.in_use[offset // self.block_size] = 0
        struct.pack_into("<I", self.buffer, offset, self.head)
        self.head = offset
