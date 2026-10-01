READ the request to implement a fixed‑block memory pool allocator in Python
INITIALIZE a memory pool with N blocks each of size B bytes
CREATE a free‑list embedded in the buffer to track available blocks
DEFINE an allocate function that RETURNS the offset of a free block OR raises a PoolExhausted exception when no blocks remain
DEFINE a free function that ACCEPTS an offset and RETURNS the block to the pool, detecting double‑free errors
WRITE tests that VERIFY allocation of all N blocks
WRITE tests that VERIFY a PoolExhausted exception on the N+1‑th allocation
WRITE tests that VERIFY proper free‑and‑reallocate cycles
WRITE tests that VERIFY detection of double‑free errors
