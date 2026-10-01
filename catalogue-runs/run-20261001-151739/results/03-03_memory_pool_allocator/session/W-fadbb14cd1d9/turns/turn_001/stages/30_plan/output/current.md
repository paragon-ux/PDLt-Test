DEFINE a FixedBlockPool class with constructor(N, B)
  INITIALIZE a bytearray buffer of size N * B
  EMBED a free‑list within the buffer using the first B bytes of each block to store the next free offset
  SET the free‑list head to offset 0
DEFINE a PoolExhausted exception subclass of Exception
DEFINE a DoubleFreeError exception subclass of Exception
DEFINE allocate() method
  IF free‑list head is None THEN RAISE PoolExhausted
  ELSE RETRIEVE current head offset
  UPDATE free‑list head to the next offset stored in the block at the current offset
  RETURN the retrieved offset
DEFINE free(offset) method
  IF offset is out of range OR not aligned to B THEN RAISE ValueError
  IF offset already appears in the free‑list THEN RAISE DoubleFreeError
  STORE current free‑list head in the block at offset
  UPDATE free‑list head to offset
PROVIDE tests
  ALLOCATE all N blocks and VERIFY each returned offset is unique and lies within the buffer range
  ATTEMPT a (N+1)st allocation and VERIFY that PoolExhausted is raised
  FREE a selected subset of allocated offsets and VERIFY those offsets can be re‑allocated
  FREE an already freed offset and VERIFY that DoubleFreeError is raised
ENSURE allocate() and free() perform no dynamic memory allocation after initialization (no calls to list.append, malloc, new, etc.)
RETURN the class definition, exception definitions, and the test suite
