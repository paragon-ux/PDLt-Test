Explanation:
When using struct.pack with the format string "I?d" without any prefix, Python uses the native byte order, size, and alignment (the "@" format). On most platforms the default alignment inserts padding to align each field to its natural boundary. The layout becomes:
- `I` (uint32) occupies bytes 0‑3.
- `?` (bool, treated as uint8) occupies byte 4.
- **Padding**: three padding bytes are added after the bool so that the following `d` (float64) starts at an address that is a multiple of 8.
- `d` then occupies bytes 8‑15.
Thus the total size is 16 bytes, not the naïve 4+1+8 = 13 bytes.

To obtain a packed size of exactly 13 bytes we must disable native alignment and use the standard size, no‑alignment format prefix "<" (little‑endian, standard sizes, no padding). The format "<I?d" packs the fields consecutively:
- 4‑byte unsigned int,
- 1‑byte bool,
- 8‑byte double,
with no padding in between, yielding a 13‑byte buffer.

Corrected code:
```python
import struct

# Use the "<" prefix to enforce standard size, no‑alignment packing
FORMAT = '<I?d'  # little‑endian, uint32, bool, float64

def pack_record(user_id: int, active: bool, score: float) -> bytes:
    """Pack the three fields into exactly 13 bytes."""
    return struct.pack(FORMAT, user_id, active, score)

def unpack_record(data: bytes):
    """Unpack a 13‑byte buffer back into the original fields."""
    return struct.unpack(FORMAT, data)

if __name__ == '__main__':
    original = (42, True, 98.6)
    packed = pack_record(*original)
    recovered = unpack_record(packed)
    print(f"Original: {original}")
    print(f"Recovered: {recovered}")
    print(f"Match: {original == recovered}")
    print(f"Packed size: {len(packed)} bytes (expected 13)")
```
Running this script prints:
```
Original: (42, True, 98.6)
Recovered: (42, True, 98.6)
Match: True
Packed size: 13 bytes (expected 13)
```
