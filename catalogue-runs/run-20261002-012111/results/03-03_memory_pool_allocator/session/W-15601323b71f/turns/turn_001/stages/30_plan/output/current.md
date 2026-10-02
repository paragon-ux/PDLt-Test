DEFINE a FixedBlockMemoryPool class
INITIALIZE the pool with a fixed buffer of N blocks each of size B bytes
SETUP a free list within the buffer to track available blocks
IMPLEMENT allocate() method that
    SEARCH the free list for a free block
    RETURN the offset of the selected block
    REMOVE the block from the free list
    RAISE PoolExhausted if the free list is empty
IMPLEMENT free(offset) method that
    VALIDATE that offset corresponds to a block within the pool
    DETECT double-free attempts and raise an appropriate exception
    INSERT the block back into the free list
ENSURE allocate() and free(offset) do NOT invoke external allocation functions or list.append after initialization, managing the free list directly within the buffer
DEFINE a custom PoolExhausted exception type
WRITE test suite that
    CREATE a pool instance with specific N and B values
    CALL allocate() N times and VERIFY each returned offset is distinct
    ATTEMPT a (N+1)th allocation and VERIFY that PoolExhausted is raised
    CALL free(offset) on a subset of allocated offsets
    CALL allocate() again to VERIFY that freed blocks are reusable
    CALL free(offset) twice on the same offset and VERIFY detection of double-free error
RUN the test suite and VERIFY all assertions pass
