ENTITIES: allocate(), free(offset), PoolExhausted, malloc, new, list.append, N, B

IMPLEMENT a fixed-block memory pool allocator in Python.
INITIALIZE the pool with a fixed buffer of N blocks each of size B bytes.
PROVIDE an allocate() method that:
    RETURNS the offset of a free block.
    RAISES PoolExhausted when no free blocks are available.
PROVIDE a free(offset) method that:
    RETURNS the block at the given offset to the pool.
ENSURE allocate() and free(offset) do NOT call malloc, new, or list.append after initialization; they MUST manage the free list directly within the buffer.
INCLUDE tests that:
    VERIFY allocation of all N blocks succeeds.
    VERIFY a PoolExhausted exception is raised on the N+1 allocation attempt.
    VERIFY correct free-and-reallocate cycles.
    VERIFY detection of double-free errors.
