READ the request for a fixed‑block memory pool allocator in Python
DEFINE a memory pool with N blocks each of size B bytes
INITIALIZE an embedded free‑list covering all N blocks
IMPLEMENT allocate() to return the offset of the next free block from the free‑list; IF no free block remains THEN raise PoolExhausted
IMPLEMENT free(offset) to return the block at the given offset to the free‑list; IF the offset is already in the free‑list THEN raise an error for double‑free
ENSURE allocate() and free() perform no dynamic memory allocation (no malloc, new, list.append, etc.)
WRITE tests that:
VERIFY allocation of all N blocks succeeds
VERIFY a subsequent allocation raises PoolExhausted
VERIFY that freeing a block allows it to be re‑allocated
VERIFY that freeing the same block twice is detected as an error
