TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a fixed-block memory pool allocator in Python: initialize a pool with N blocks of size B bytes, provide allocate() returning the offset of a free block or raising PoolExhausted, provide free(offset) to return a block, enforce that allocate/free do not use dynamic memory allocation (no malloc, new, list.append) and use an embedded free-list, and include tests verifying allocation of all N blocks, PoolExhausted on N+1 allocation, free-and-reallocate cycles, and double-free detection.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- N
- B
- allocate
- free
- PoolExhausted
