TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a fixed-block memory pool allocator in Python with a pool initialized to N blocks each of size B bytes. Provide an allocate() function that returns the offset of a free block or raises a PoolExhausted exception, and a free(offset) function that returns a block to the pool. After initialization, allocate and free must not use dynamic memory allocation functions such as malloc, new, or list.append, instead using a free-list embedded in the buffer. Include tests that verify allocation of all N blocks, raising PoolExhausted on an N+1th allocation, proper free-and-reallocate cycles, and detection of double-free errors.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- allocate
- free
- PoolExhausted
