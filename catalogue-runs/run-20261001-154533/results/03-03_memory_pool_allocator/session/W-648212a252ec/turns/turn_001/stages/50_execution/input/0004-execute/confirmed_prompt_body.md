IMPLEMENT a fixed‑block memory pool allocator in Python that initializes a buffer containing N blocks each of size B bytes.
PROVIDE an allocate() function that returns the offset of a free block.
RAISE a PoolExhausted exception when the pool is exhausted.
PROVIDE a free(offset) function that returns a block to the pool.
ENSURE that after initialization allocate() and free(offset) do NOT use malloc, new, or list.append; manage a free‑list embedded within the buffer itself.
INCLUDE tests that verify allocation of all N blocks.
VERIFY that calling allocate() after all N blocks have been allocated raises PoolExhausted on the N+1‑th call.
VERIFY that freeing blocks and re‑allocating works correctly.
DETECT a double‑free error when attempting to free the same offset twice.
