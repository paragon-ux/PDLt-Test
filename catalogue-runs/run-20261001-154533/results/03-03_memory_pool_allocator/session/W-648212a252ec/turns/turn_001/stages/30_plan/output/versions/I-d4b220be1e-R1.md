VALIDATE the parameters N and B as positive integers
INITIALIZE a contiguous buffer of size N*B bytes to serve as the memory pool
EMBED a free‑list inside the buffer by linking each block to the next block offset
DEFINE an allocate() operation that removes the head of the free‑list and returns its offset
RAISE a PoolExhausted exception when the free‑list is empty
DEFINE a free(offset) operation that inserts the block at offset back into the free‑list
DETECT a double‑free error by checking whether the offset is already present in the free‑list before insertion
CONSTRUCT unit‑test cases that allocate all N blocks sequentially
VERIFY that a subsequent allocate() call raises PoolExhausted after N allocations
VERIFY that freeing selected blocks and calling allocate() again returns the previously freed offsets
VERIFY that attempting to free the same offset twice triggers the double‑free detection logic
