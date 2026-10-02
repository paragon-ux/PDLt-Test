The following struct packing code silently produces wrong values when reading data back. The bug is an alignment/padding issue. Diagnose it and fix it.

```python
import struct

# Write a record: user_id (uint32), active (bool/uint8), score (float64)
def pack_record(user_id, active, score):
    return struct.pack('I?d', user_id, active, score)

def unpack_record(data):
    user_id, active, score = struct.unpack('I?d', data)
    return user_id, active, score

# Test
original = (42, True, 98.6)
packed = pack_record(*original)
recovered = unpack_record(packed)
print(f"Original: {original}")
print(f"Recovered: {recovered}")
print(f"Match: {original == recovered}")
print(f"Packed size: {len(packed)} bytes (expected: 4+1+8 = 13)")
```

Explain why the packed size may not be 13 bytes and why values may read incorrectly. Fix it with explicit padding control.
