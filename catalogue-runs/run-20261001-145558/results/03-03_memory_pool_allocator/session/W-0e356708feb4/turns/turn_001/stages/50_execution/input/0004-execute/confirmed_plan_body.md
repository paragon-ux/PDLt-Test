READ the request to implement a fixed‑block memory pool allocator in Python
INITIALIZE a memory pool data structure with N blocks each of size B bytes
EMBED a free‑list within the pool buffer to track available blocks
DEFINE an allocate operation that RETURNS the offset of a free block OR raises a PoolExhausted exception when no blocks remain
DEFINE a free operation that ACCEPTS an offset and RETURNS the block to the pool, detecting double‑free errors
WRITE tests that VERIFY allocation of all N blocks
WRITE tests that VERIFY a PoolExhausted exception on the N+1‑th allocation
WRITE tests that VERIFY proper free‑and‑reallocate cycles
WRITE tests that VERIFY detection of double‑free errors
