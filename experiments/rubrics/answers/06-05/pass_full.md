**Why it isn't 13 bytes.** With no prefix, `struct` uses native mode (`@`): sizes *and alignment* follow the C compiler. After the 4-byte `I` and the 1-byte `?`, the 8-byte `d` must start on an 8-byte boundary, so 3 padding bytes are inserted: 4 + 1 + 3 + 8 = 16 (`struct.calcsize('I?d') == 16` on x86-64).

**When values read wrongly.** On one machine, packing and unpacking with the same native format round-trips fine. The problem appears when the bytes cross a boundary: a reader expecting the 13-byte packed layout (a file format, a network peer, another language) reads the double starting at offset 5 instead of 8, getting garbage, or `struct.unpack` raises `struct.error` because 16 != 13 bytes. Native layout also varies by platform and byte order.

**Fix: explicit layout.**
```python
import struct
RECORD = struct.Struct('<I?d')   # little-endian, standard sizes, no padding: 13 bytes

def pack_record(user_id, active, score):
    return RECORD.pack(user_id, active, score)

def unpack_record(data):
    return RECORD.unpack(data)

original = (42, True, 98.6)
packed = pack_record(*original)
assert len(packed) == 13 == RECORD.size
assert unpack_record(packed) == original
```
If padding is wanted (e.g. to match a C struct), make it explicit: `'<I?3xd'` (16 bytes, same on every platform). Always fix the byte order too (`<` or `!`).
