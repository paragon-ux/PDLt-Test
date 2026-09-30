DEFINE a fixed‑block memory pool class with parameters N (number of blocks) and B (block size)
INITIALIZE an internal bytearray or buffer of size N*B to hold the raw memory
CONSTRUCT a free‑list data structure that tracks offsets of all N blocks, initially containing offsets 0, B, 2*B, … , (N‑1)*B
IMPLEMENT allocate() METHOD
IF the free‑list is non‑empty THEN POP the next free offset and RETURN it
ELSE RAISE a PoolExhausted exception
IMPLEMENT free(offset) METHOD
IF offset is not currently in the free‑list AND offset is a valid block start THEN PUSH offset back onto the free‑list
ELSE RAISE an error for double‑free or invalid offset
WRITE unit tests
TEST that allocating N times returns N distinct offsets and leaves the free‑list empty
TEST that a subsequent allocate() call raises PoolExhausted
TEST that freeing a previously allocated offset restores it to the free‑list and a subsequent allocate() returns that offset again
TEST that invoking free() twice on the same offset raises the double‑free error
