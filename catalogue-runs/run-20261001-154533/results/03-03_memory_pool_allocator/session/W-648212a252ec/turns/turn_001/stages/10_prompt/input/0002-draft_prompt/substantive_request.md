TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement in Python a fixed‑block memory pool allocator that initializes a buffer containing N blocks each of size B bytes. Provide an allocate() function that returns the offset of a free block and raises the exception PoolExhausted when the pool is exhausted. Provide a free(offset) function that returns a block to the pool. After initialization, allocate() and free() must not use malloc, new, or list.append; instead they must manage a free‑list embedded within the buffer itself. Include tests that verify allocation of all N blocks, that calling allocate() after all N blocks have been allocated raises PoolExhausted (i.e., on the N+1‑th call), that freeing blocks and re‑allocating works correctly, and that attempting to free the same offset twice is detected as a double‑free error.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- allocate()
- free(offset)
- PoolExhausted
- N
- B
- malloc
- new
- list.append
- offset
