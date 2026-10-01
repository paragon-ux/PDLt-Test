DEFINE a fixed‑block memory pool allocator in Python with a buffer containing N blocks each of size B bytes.
PROVIDE a function allocate() that returns an int offset of a free block.
RAISE a PoolExhausted exception when the pool is exhausted.
PROVIDE a function free(offset) that returns the block at the given offset to the pool.
ENSURE that after initialization, allocate() and free() do not invoke any dynamic allocation calls such as malloc, new, or list.append.
MANAGE a free‑list embedded within the buffer itself.
INCLUDE tests that verify allocation of all N blocks.
VERIFY that a PoolExhausted exception is raised on the (N+1)st allocation.
VERIFY that freed blocks can be re‑allocated correctly.
VERIFY that double‑free attempts are detected.
